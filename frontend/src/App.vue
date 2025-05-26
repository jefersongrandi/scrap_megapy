<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-toolbar-title>Resultados da Megasena</v-toolbar-title>
    </v-app-bar>

    <v-main>
      <v-container>
        <div v-if="carregando" class="text-center my-8">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
          <p class="mt-2">Carregando resultados...</p>
        </div>

        <div v-else>
          <h1 class="text-center mb-6">Último Sorteio</h1>
          
          <!-- Seção principal com último resultado e estatísticas -->
          <v-row>
            <!-- Coluna da esquerda - Último resultado -->
            <v-col cols="12" md="6">
              <MegasenaResult 
                v-if="ultimoResultado" 
                :resultado="ultimoResultado" 
                :meusJogos="meusJogos"
              />
            </v-col>
            
            <!-- Coluna da direita - Estatísticas -->
            <v-col cols="12" md="6">
              <v-card class="mb-4 position-relative">
                <v-card-title class="text-center">
                  Estatísticas dos Últimos 50 Sorteios
                </v-card-title>
                
                <!-- Loader específico para estatísticas -->
                <div v-if="carregandoEstatisticas" class="estatisticas-loader">
                  <div class="loader-overlay"></div>
                  <v-progress-circular
                    indeterminate
                    color="primary"
                    size="70"
                  ></v-progress-circular>
                </div>
                
                <v-card-text>
                  <div v-if="estatisticas">
                    <h3 class="text-center mb-3">Dezenas Mais Sorteadas</h3>
                    <div class="d-flex flex-wrap justify-center mb-5">
                      <div
                        v-for="(item, index) in estatisticas.dezenas_mais_sorteadas"
                        :key="'mais-' + index"
                        class="numero-estatistica"
                      >
                        <div class="numero-circulo">{{ item[0] }}</div>
                        <div class="numero-frequencia">{{ item[1] }}x</div>
                      </div>
                    </div>
                    
                    <h3 class="text-center mb-3 mt-5">Dezenas Menos Sorteadas</h3>
                    <div class="d-flex flex-wrap justify-center">
                      <div
                        v-for="(item, index) in estatisticas.dezenas_menos_sorteadas"
                        :key="'menos-' + index"
                        class="numero-estatistica"
                      >
                        <div class="numero-circulo cinza">{{ item[0] }}</div>
                        <div class="numero-frequencia">{{ item[1] }}x</div>
                      </div>
                    </div>
                    
                    <div class="text-center mt-5">
                      <p><strong>Concursos analisados:</strong> {{ estatisticas.concursos_analisados }}</p>
                      <p><strong>Período:</strong> {{ estatisticas.periodo.primeiro_concurso }} a {{ estatisticas.periodo.ultimo_concurso }}</p>
                    </div>
                  </div>
                  <div v-else class="text-center">
                    <p>Nenhuma estatística disponível</p>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          <h2 class="text-center my-6">Outros Sorteios</h2>
          
          <!-- Resultados anteriores -->
          <div class="d-flex flex-wrap justify-center">
            <v-col 
              v-for="(resultado, index) in resultadosAnteriores" 
              :key="index"
              cols="12" sm="6" md="4"
            >
              <MegasenaResult 
                :resultado="resultado" 
                :meusJogos="meusJogos"
                :titulo="`MegaSena: ${resultado.data_sorteio} - ${resultado.concurso}`"
              />
            </v-col>
          </div>
        </div>
      </v-container>
    </v-main>

    <v-footer app>
      <v-col class="text-center">
        {{ new Date().getFullYear() }} — <strong>Verificador de Resultados da Megasena</strong>
      </v-col>
    </v-footer>
  </v-app>
</template>

<script>
import MegasenaResult from './components/MegasenaResult.vue'
import MegasenaService from './services/MegasenaService'
import axios from 'axios'

export default {
  name: 'App',
  components: {
    MegasenaResult
  },
  data() {
    return {
      carregando: true,
      carregandoEstatisticas: false,
      resultados: [],
      estatisticas: null,
      meusJogos: [
        [3, 5, 17, 24, 30, 51, 52],
        [4, 14, 29, 32, 43, 44, 47],
        [11, 25, 42, 46, 49, 54],
        [1, 13, 21, 33, 35, 44]
      ]
    }
  },
  computed: {
    ultimoResultado() {
      return this.resultados.length > 0 ? this.resultados[0] : null;
    },
    resultadosAnteriores() {
      return this.resultados.length > 1 ? this.resultados.slice(1) : [];
    }
  },
  async created() {
    await this.carregarResultados();
    await this.carregarEstatisticas();
  },
  methods: {
    async carregarResultados() {
      try {
        this.carregando = true;
        const historicoData = await MegasenaService.getHistoricoMegasena();
        
        // Processar os resultados do Firestore
        this.resultados = historicoData
          .filter(item => item.conteudo && item.metadados && item.metadados.fonte === 'api_caixa')
          .map(item => {
            // Garantir que temos um objeto válido
            const conteudo = typeof item.conteudo === 'string' 
              ? JSON.parse(item.conteudo) 
              : item.conteudo;
            
            return {
              concurso: conteudo.concurso || 'N/A',
              data_sorteio: conteudo.data_sorteio || 'N/A',
              dezenas: conteudo.dezenas || [],
              premiacao: conteudo.premiacao || {},
              acumulado: conteudo.acumulado || false
            };
          });
      } catch (error) {
        console.error('Erro ao carregar resultados:', error);
        this.resultados = [];
      } finally {
        this.carregando = false;
      }
    },
    async carregarEstatisticas() {
      try {
        this.carregandoEstatisticas = true;
        const response = await axios.get('https://api-mty2yurbea-uc.a.run.app/megasena/estatisticas?ultimos=50');
        this.estatisticas = response.data;
      } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
        this.estatisticas = null;
      } finally {
        this.carregandoEstatisticas = false;
      }
    }
  }
}
</script>

<style>
@import '@mdi/font/css/materialdesignicons.css';

.numero-estatistica {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 5px 10px;
}

.numero-circulo {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 5px;
  background-color: #f44336;
  color: white;
  font-weight: bold;
}

.numero-circulo.cinza {
  background-color: #9e9e9e;
}

.numero-frequencia {
  font-size: 12px;
  font-weight: bold;
}

.position-relative {
  position: relative;
}

.estatisticas-loader {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.loader-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.7);
  z-index: 1;
}

.estatisticas-loader .v-progress-circular {
  z-index: 2;
}
</style>
