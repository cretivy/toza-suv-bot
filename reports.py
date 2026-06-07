import pandas as pd
from datetime import datetime
import data_manager
import os

def generate_excel_report():
    orders = data_manager.get_orders()
    if not orders:
        return None

    # Convert to DataFrame
    df = pd.DataFrame(orders)
    
    # Process timestamps
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['sana'] = df['timestamp'].dt.date
    df['vaqt'] = df['timestamp'].dt.time
    
    # Process location
    df['lat'] = df['location'].apply(lambda x: x.get('lat') if isinstance(x, dict) else None)
    df['lon'] = df['location'].apply(lambda x: x.get('lon') if isinstance(x, dict) else None)
    
    # Reorder and rename columns
    columns = {
        'timestamp': 'Vaqt',
        'customer_id': 'Mijoz ID',
        'quantity': 'Hajmi (soni)',
        'phone': 'Telefon',
        'payment_method': 'To\'lov usuli',
        'driver_id': 'Haydovchi ID',
        'lat': 'Latitude',
        'lon': 'Longitude'
    }
    
    df_final = df[list(columns.keys())].rename(columns=columns)
    
    filename = f"hisobot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    file_path = os.path.join(os.getcwd(), filename)
    
    # Export to Excel
    df_final.to_excel(file_path, index=False)
    
    return file_path
