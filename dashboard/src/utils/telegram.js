export const getTelegramUser = () => {
  const tg = window.Telegram?.WebApp;
  if (!tg) return null;
  return tg.initDataUnsafe?.user;
};

export const getInitData = () => {
  return window.Telegram?.WebApp?.initData || '';
};

export const expandWebApp = () => {
  window.Telegram?.WebApp?.expand();
};
