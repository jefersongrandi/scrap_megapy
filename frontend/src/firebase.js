import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

// Configuração do Firebase
const firebaseConfig = {
  apiKey: "AIzaSyAKzJokuPhNI3LaS1dMfhokmVRiP6QrSxI",
  authDomain: "mega-sena-40cff.firebaseapp.com",
  projectId: "mega-sena-40cff",
  storageBucket: "mega-sena-40cff.firebasestorage.app",
  messagingSenderId: "773859429624",
  appId: "1:773859429624:web:d702b01078d9ec619dbf0d"
};

// Inicializar Firebase
const app = initializeApp(firebaseConfig);

// Inicializar Firestore
const db = getFirestore(app);

export { db }; 