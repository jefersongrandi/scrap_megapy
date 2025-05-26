import { db } from '../firebase';
import { collection, getDocs, query, orderBy, limit } from 'firebase/firestore';

class MegasenaService {
  // Padrão Singleton para garantir uma única instância
  static instance = null;

  constructor() {
    if (MegasenaService.instance) {
      return MegasenaService.instance;
    }
    MegasenaService.instance = this;
  }

  // Busca dados diretamente do Firestore
  async getHistoricoMegasena() {
    try {
      const q = query(
        collection(db, 'scraping_results'),
        orderBy('conteudo.data_sorteio', 'desc'),
        limit(150)
      );

      const querySnapshot = await getDocs(q);
      const resultados = [];

      querySnapshot.forEach((doc) => {
        const dados = doc.data();
        dados.id = doc.id;
        resultados.push(dados);
      });

      return resultados;
    } catch (error) {
      console.error('Erro ao buscar histórico do Firestore:', error);
      return [];
    }
  }

  // Verifica acertos em um jogo comparado com o resultado
  verificarAcertos(dezenasSorteadas, meusJogos) {
    if (!dezenasSorteadas || !meusJogos) return [];

    return meusJogos.map(jogo => {
      const dezenasSorteadasArray = Array.isArray(dezenasSorteadas) 
        ? dezenasSorteadas 
        : dezenasSorteadas.split(',');
      
      const jogoDezenas = Array.isArray(jogo) 
        ? jogo.map(num => num.toString()) 
        : jogo;
      
      const acertos = jogoDezenas.filter(dezena => 
        dezenasSorteadasArray.includes(dezena.toString())
      );
      
      return {
        jogo: jogoDezenas,
        acertos: acertos.length,
        dezenasAcertadas: acertos
      };
    });
  }
}

// Exporta uma instância única
export default new MegasenaService(); 