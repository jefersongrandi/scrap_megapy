<template>
  <v-card class="mb-4">
    <v-card-title class="text-center">
      {{ titulo }}
    </v-card-title>
    <v-card-text>
      <div class="text-center">
        <p>MegaSena: {{ resultadoFormatado }}</p>
        <div class="d-flex flex-wrap justify-center">
          <div
            v-for="(numero, index) in resultado.dezenas"
            :key="index"
            :class="['numero-circulo', isNumeroSorteado(numero) ? 'sorteado' : '']"
          >
            {{ numero }}
          </div>
        </div>
      </div>
      
      <div class="text-center mt-4">
        <p>Meus jogos</p>
        <div class="d-flex flex-wrap justify-center mb-3" v-for="(jogo, jogoIndex) in meusJogos" :key="jogoIndex">
          <div
            v-for="(numero, index) in jogo"
            :key="index"
            :class="['numero-circulo', isNumeroSorteado(numero.toString()) ? 'sorteado' : '']"
          >
            {{ numero }}
          </div>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'MegasenaResult',
  props: {
    resultado: {
      type: Object,
      required: true
    },
    meusJogos: {
      type: Array,
      required: true
    },
    titulo: {
      type: String,
      default: 'Último Sorteio'
    }
  },
  computed: {
    resultadoFormatado() {
      if (!this.resultado || !this.resultado.data_sorteio) return '';
      return `${this.resultado.data_sorteio} - ${this.resultado.concurso}`;
    }
  },
  methods: {
    isNumeroSorteado(numero) {
      return this.resultado.dezenas && this.resultado.dezenas.includes(numero);
    }
  }
}
</script>

<style scoped>
.numero-circulo {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 5px;
  background-color: #e0e0e0;
  color: #000;
  font-weight: bold;
}

.sorteado {
  background-color: #f44336;
  color: white;
}
</style> 