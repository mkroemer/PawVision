import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Import translation files
import en from './locales/en.json';

const resources = {
  en: {
    translation: en,
  },
  de: {
    translation: en, // Use English for now, German translations can be added later
  },
};

// Get saved language or use browser language
const savedLanguage = localStorage.getItem('pawvision-language');
const browserLanguage = navigator.language.split('-')[0]; // Get 'en' from 'en-US'
const defaultLanguage = savedLanguage || (resources[browserLanguage as keyof typeof resources] ? browserLanguage : 'en');

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: defaultLanguage,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
