import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

import config
import data_manager
import reports

# logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# --- FSM for Customer ---
class OrderFlow(StatesGroup):
    waiting_for_quantity = State()
    waiting_for_phone = State()
    waiting_for_location = State()
    waiting_for_payment = State()

# --- Custom Filters ---
class IsAdmin(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id == config.ADMIN_ID

class IsDriver(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in config.DRIVER_IDS

class IsCustomer(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id != config.ADMIN_ID and message.from_user.id not in config.DRIVER_IDS

# --- KEYBOARDS ---
def get_driver_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Smenani boshlash"), KeyboardButton(text="Smenani tugatish")]
        ],
        resize_keyboard=True
    )

def get_admin_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Jami mijozlar soni")],
            [KeyboardButton(text="Hozir kim smenada?")],
            [KeyboardButton(text="Hisobotlarni yuklash 📊")],
            [KeyboardButton(text="Dashboardni ochish 🌐")],
            [KeyboardButton(text="Smenani majburiy tugatish")]
        ],
        resize_keyboard=True
    )

def get_phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True
    )
def get_location_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Lokatsiya yuborish", request_location=True)]
        ],
        resize_keyboard=True
    )
def get_payment_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Naqd 💵")],
            [KeyboardButton(text="Click 🔵"), KeyboardButton(text="Payme 💳")]
        ],
        resize_keyboard=True
    )
def get_nav_kb(lat, lon, order_id):
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🗺 Yandex", url=f"https://yandex.com/maps/?pt={lon},{lat}&z=16&l=map"),
                types.InlineKeyboardButton(text="🗺 Google", url=f"https://www.google.com/maps/search/?api=1&query={lat},{lon}")
            ],
            [
                types.InlineKeyboardButton(text="🚚 Yo'lga chiqdim", callback_data=f"order_onway_{order_id}"),
                types.InlineKeyboardButton(text="✅ Yetkazib berildi", callback_data=f"order_done_{order_id}")
            ]
        ]
    )

# ==================================================
# 3. ADMIN LOGIKASI
# ==================================================
@dp.message(IsAdmin(), Command("start"))
@dp.message(IsAdmin(), F.text == "Admin Panel")
async def admin_start(message: types.Message):
    await message.answer("Xush kelibsiz Super Admin! Boshqaruv paneli:", reply_markup=get_admin_kb())

@dp.message(IsAdmin(), F.text == "Jami mijozlar soni")
async def admin_customers_count(message: types.Message):
    count = data_manager.get_customers_count()
    await message.answer(f"Jami mijozlar soni: {count} ta")

@dp.message(IsAdmin(), F.text == "Hozir kim smenada?")
async def admin_current_driver(message: types.Message):
    driver_id = data_manager.get_active_driver_id()
    if driver_id:
        await message.answer(f"Hozirgi faol haydovchi ID: {driver_id}")
    else:
        await message.answer("Hozir smenada hech kim yo'q.")

@dp.message(IsAdmin(), F.text == "Smenani majburiy tugatish")
async def admin_force_stop(message: types.Message):
    data_manager.set_active_driver_id(None)
    await message.answer("Smena muvaffaqiyatli yakunlandi (NULL qilindi).")

@dp.message(IsAdmin(), F.text == "Hisobotlarni yuklash 📊")
async def admin_export_reports(message: types.Message):
    await message.answer("Hisobot tayyorlanmoqda, kuting...")
    try:
        file_path = reports.generate_excel_report()
        if file_path and os.path.exists(file_path):
            await message.answer_document(types.FSInputFile(file_path), caption="Barcha buyurtmalar hisoboti")
            # Optional: remove file after sending
            # os.remove(file_path)
        else:
            await message.answer("Hozircha buyurtmalar mavjud emas.")
    except Exception as e:
        logging.error(f"Error exporting report: {e}")
        await message.answer(f"Xatolik yuz berdi: {e}")

@dp.message(IsAdmin(), F.text == "Dashboardni ochish 🌐")
async def admin_open_dashboard(message: types.Message):
    # This will be pointing to the Mini App URL. For local dev, we'll use a placeholder or local IP if known.
    # We use WebAppInfo to open the Mini App.
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Dashboardni ko'rish", web_app=types.WebAppInfo(url="https://grottolike-isogonally-marjory.ngrok-free.dev"))]
        ]
    )
    await message.answer("Admin Dashboardni ochish uchun quyidagi tugmani bosing:", reply_markup=kb)

# ==================================================
# 4. SMART REMINDERS & BACKGROUND TASKS
# ==================================================
async def check_reminders():
    state = data_manager.get_state()
    customers = state.get("customers", [])
    for user_id in customers:
        last_date = data_manager.get_last_order_date(user_id)
        if not last_date:
            continue
        
        avg_days = data_manager.get_average_interval(user_id)
        if datetime.now() > last_date + timedelta(days=avg_days):
            # Check if we already reminded recently (e.g., today)
            # For simplicity, we just send it once a day
            try:
                kb = types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [types.InlineKeyboardButton(text="🔄 Oxirgi buyurtmani takrorlash", callback_data="repeat_last_order")]
                    ]
                )
                await bot.send_message(user_id, f"Assalomu alaykum! Suvingiz tugab qolgan bo'lishi mumkin. Buyurtma berishni unutmadingizmi? 😊", reply_markup=kb)
            except Exception as e:
                logging.error(f"Error sending reminder to {user_id}: {e}")

@dp.callback_query(F.data == "repeat_last_order")
async def repeat_order(callback: types.CallbackQuery, state: FSMContext):
    user_orders = [o for o in data_manager.get_orders() if o['customer_id'] == callback.from_user.id]
    if not user_orders:
        await callback.answer("Avvalgi buyurtmalar topilmadi.")
        return
    
    last_order = user_orders[-1]
    await state.update_data(
        quantity=last_order['quantity'],
        phone=last_order['phone'],
        location=last_order['location']
    )
    await callback.message.answer(f"Oxirgi buyurtmangiz tanlandi:\n- Hajmi: {last_order['quantity']}\n- Tel: {last_order['phone']}\n\nTo'lov usulini tanlang:", reply_markup=get_payment_kb())
    await state.set_state(OrderFlow.waiting_for_payment)
    await callback.answer()

@dp.callback_query(F.data.startswith("order_onway_"))
async def order_onway(callback: types.CallbackQuery):
    order_id = callback.data.replace("order_onway_", "")
    data_manager.update_order_status(order_id, "In Progress")
    
    # Update physical message text/keyboard
    new_text = callback.message.text + "\n\n🔄 **Holati**: Yo'lda 🚚"
    await callback.message.edit_text(new_text, reply_markup=callback.message.reply_markup, parse_mode="Markdown")
    await callback.answer("Status yangilandi: Yo'lda")

@dp.callback_query(F.data.startswith("order_done_"))
async def order_done(callback: types.CallbackQuery):
    order_id = callback.data.replace("order_done_", "")
    data_manager.update_order_status(order_id, "Delivered")
    
    # Disable buttons and mark as finished
    new_text = callback.message.text.split("\n\n")[0] + "\n\n✅ **Holati**: Yetkazib berildi"
    await callback.message.edit_text(new_text, reply_markup=None, parse_mode="Markdown")
    await callback.answer("Buyurtma yopildi!")

# ==================================================
# 2. HAYDOVCHILAR LOGIKASI
# ==================================================
@dp.message(IsDriver(), Command("start"))
async def driver_start(message: types.Message):
    await message.answer("Assalomu alaykum, Haydovchi! Smenani boshlash uchun quyidagi tugmalardan foydalaning:", reply_markup=get_driver_kb())

@dp.message(IsDriver(), F.text == "Smenani boshlash")
@dp.message(IsDriver(), Command("start_shift"))
async def driver_start_shift(message: types.Message):
    data_manager.set_active_driver_id(message.from_user.id)
    warning_text = (
        "✅ Smena boshlandi!\n\n"
        "⚠️ **DIQQAT**: Suvni mijozga haqiqatda yetkazib bermasdan turib, "
        "'Yetkazib berildi' tugmasini bosmang! Hisobotlar aniq yuritiladi."
    )
    await message.answer(warning_text, reply_markup=get_driver_kb(), parse_mode="Markdown")

@dp.message(IsDriver(), F.text == "Smenani tugatish")
@dp.message(IsDriver(), Command("end_shift"))
async def driver_end_shift(message: types.Message):
    current_active = data_manager.get_active_driver_id()
    if current_active == message.from_user.id:
        data_manager.set_active_driver_id(None)
        await message.answer("Smenani tugatdingiz.", reply_markup=get_driver_kb())
    else:
        await message.answer("Siz hozir smenada emassiz.")

# ==================================================
# 1. MIJOZ LOGIKASI
# ==================================================
@dp.message(IsCustomer(), Command("start"))
async def customer_start(message: types.Message, state: FSMContext):
    data_manager.add_customer(message.from_user.id)
    await message.answer("Assalomu alaykum! Suv miqdorini kiriting (masalan: 2 ta):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(OrderFlow.waiting_for_quantity)

@dp.message(OrderFlow.waiting_for_quantity)
async def process_quantity(message: types.Message, state: FSMContext):
    await state.update_data(quantity=message.text)
    await message.answer("Iltimos, telefon raqamingizni yuboring:", reply_markup=get_phone_kb())
    await state.set_state(OrderFlow.waiting_for_phone)

@dp.message(OrderFlow.waiting_for_phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("Iltimos, GEOLOKATSIYAtingizni (Location) yuboring:", reply_markup=get_location_kb())
    await state.set_state(OrderFlow.waiting_for_location)

@dp.message(OrderFlow.waiting_for_location, F.location)
async def process_location(message: types.Message, state: FSMContext):
    await state.update_data(
        location={"lat": message.location.latitude, "lon": message.location.longitude}
    )
    await message.answer("To'lov usulini tanlang:", reply_markup=get_payment_kb())
    await state.set_state(OrderFlow.waiting_for_payment)

@dp.message(OrderFlow.waiting_for_payment)
async def process_payment(message: types.Message, state: FSMContext):
    payment_method = message.text
    if payment_method not in ["Naqd 💵", "Click 🔵", "Payme 💳"]:
        await message.answer("Iltimos, tugmalardan birini tanlang!", reply_markup=get_payment_kb())
        return

    user_data = await state.get_data()
    quantity = user_data['quantity']
    phone = user_data['phone']
    location = user_data['location']
    
    # Save order
    order_info = {
        "customer_id": message.from_user.id,
        "quantity": quantity,
        "phone": phone,
        "location": location,
        "payment_method": payment_method,
        "driver_id": data_manager.get_active_driver_id()
    }
    data_manager.add_order(order_info)

    # Prepare Notification Text for Driver
    payment_status_text = ""
    if "Naqd" in payment_method:
        payment_status_text = "To'lov: Naqd to'lash zarur 💵"
    else:
        payment_status_text = "To'lov: Kartadan avtomatik to'langan ✅"

    # Notify Customer
    await message.answer("Buyurtma qabul qilindi, tez orada yetkaziladi", reply_markup=ReplyKeyboardRemove())
    
    # Notify Active Driver
    active_driver_id = data_manager.get_active_driver_id()
    if active_driver_id:
        order_text = (
            f"📦 YANGI BUYURTMA #{order_info['id']}\n"
            f"- Hajmi: {quantity} ta idish\n"
            f"- Mijoz telefoni: {phone}\n"
            f"- {payment_status_text}\n"
            "- Lokatsiya: (Pastdagi tugmalar)"
        )
        try:
            await bot.send_message(active_driver_id, order_text, reply_markup=get_nav_kb(location['lat'], location['lon'], order_info['id']))
            await bot.send_location(active_driver_id, latitude=location['lat'], longitude=location['lon'])
        except Exception as e:
            logging.error(f"Error sending order to driver: {e}")
            await bot.send_message(config.ADMIN_ID, f"XATO: Haydovchiga xabar yuborib bo'lmadi! ID: {active_driver_id}")
    else:
        # Notify Admin if no active driver
        admin_text = (
            "OGOHLANTIRISH: Smenada haydovchi yo'q! Yangi buyurtma keldi.\n"
            f"- Hajmi: {quantity}\n"
            f"- Tel: {phone}\n"
            f"- {payment_status_text}"
        )
        await bot.send_message(config.ADMIN_ID, admin_text)
        await bot.send_location(config.ADMIN_ID, latitude=location['lat'], longitude=location['lon'])

    await state.clear()

# Handle text instead of contact/location
@dp.message(OrderFlow.waiting_for_phone)
async def phone_error(message: types.Message):
    await message.answer("Iltimos, button orqali kontakt yuboring!", reply_markup=get_phone_kb())

@dp.message(OrderFlow.waiting_for_location)
async def location_error(message: types.Message):
    await message.answer("Iltimos, button orqali geolokatsiya yuboring!", reply_markup=get_location_kb())

# --- RUN BOT ---
async def main():
    scheduler = AsyncIOScheduler()
    # Check every day at 10:00 AM
    scheduler.add_job(check_reminders, 'cron', hour=10, minute=0)
    scheduler.start()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
