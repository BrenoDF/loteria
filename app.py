import random
import requests
import time 
import sqlite3
from os import system

with sqlite3.connect('loteria.db') as conn:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jogos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numeros TEXT NOT NULL,
            jogo TEXT NOT NULL,
            data_jogo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
_session = requests.Session()
        
class Jogo:
    def __init__(self, numeros, nome_jogo, qtd_num, num_max, num_min, qtd_max_num, qtd_min_num):
        self._numeros = numeros
        self._nome_jogo = nome_jogo
        self._quantidade_num = qtd_num
        self._numero_maximo = num_max
        self._numero_minimo = num_min
        self._quantidade_maxima_numeros = qtd_max_num
        self._quantidade_minima_numeros = qtd_min_num
        
    @property
    def numeros(self):
        return self._numeros
    
    @property
    def jogo(self):
        return self._nome_jogo
    
    def ver_quantidade_numeros(self):
        return self._quantidade_num
    
    def setar_qtd_num(self, qtd_num):
        if self._quantidade_minima_numeros <= qtd_num <= self._quantidade_maxima_numeros:
            self._quantidade_num = qtd_num
        else:
            raise ValueError(f"A quantidade de números deve ser entre {self._quantidade_minima_numeros} e {self._quantidade_maxima_numeros}.")
    
    def pegar_api(self, concurso: int | str = 'latest'):
        url = f'https://loteriascaixa-api.herokuapp.com/api/{self.jogo}/{concurso}'
        try:
            resposta = _session.get(url)
            data = resposta.json()
            return data
        except requests.exceptions.RequestException as e:
            print(f"Erro: {e}")
            return None
    
    def ultimos_jogos(self, qtd: int = 10):
        ultimo = self.pegar_api()
        if not ultimo or 'concurso' not in ultimo:
            print("Erro ao obter o último concurso. Verifique a internet ou fale com o administrador.")
            return []
        
        ultimo_jogo = ultimo['concurso']
        ultimos_jogos = []
        for i in range(ultimo_jogo - (qtd-1), ultimo_jogo + 1):
            data = self.pegar_api(i)
            ultimos_jogos.append(data['dezenas'])
            time.sleep(random.uniform(0.5, 1.1))
        return ultimos_jogos
    
    def estatisticas(self, qtd_concursos: int = 50):
        ultimos_jogos = self.ultimos_jogos(qtd_concursos)
        dic_numeros = {}
        for num in range(self._numero_minimo, self._numero_maximo + 1):
            for i, concurso in enumerate(reversed(ultimos_jogos)):
                if f"{num:02d}" in concurso:
                    dic_numeros[num] = i
                    break
        
        num_menos_aparicoes = dict(sorted(dic_numeros.items(), key = lambda x: x[1], reverse = True)[:10])
        
        return num_menos_aparicoes
    
    def painel(self):
        while True:
            user_input = input(
            f"""

                    {self.jogo.capitalize()}               
                Qtd. de Números: {str(self.ver_quantidade_numeros()).ljust(9)}
            +======================================+
            |  [0] Gerar números                   |
            |  [1] Alterar qtd de números          |
            |  [2] Ver últimos jogos gerados       |
            |  [3] Ver últimos jogos sorteados     |
            |  [4] Estatísticas                    |
            |  [q] Sair                            |
            +--------------------------------------+
            > Escolha uma opção:

            """
            )
            system('cls')
            
            match user_input:
                case "0":
                    numeros_gerados = self.gerar_numeros()
                    print(f"Números gerados\nJogue com: {sorted(numeros_gerados)}\nBoa sorte! \n")
                    input("Pressione Enter para continuar...")
                    system('cls')
                case "1":
                    try:
                        nova_qtd = int(input("Digite a nova quantidade de números: "))
                        self.setar_qtd_num(nova_qtd)
                        print(f"Quantidade de números alterada para {nova_qtd}.\n")
                    except ValueError as ve:
                        print(f"Erro: {ve}\n")
                case "2":
                    jogos_gerados = self.ultimos_jogos_gerados()
                    for jogo in jogos_gerados:
                        print(f"Números: {jogo[0]} | Data: {jogo[1]}")
                    input("Pressione Enter para continuar...")
                    system('cls')
                case "3":
                    print("Buscando...")
                    jogos_sorteados = self.ultimos_jogos()
                    for i, jogo in enumerate(jogos_sorteados, 1):
                        print(f"Concurso {i}: {jogo}")
                    input("Pressione Enter para continuar...")
                    system('cls')
                case "4":
                    print("Calculando estatísticas...")
                    ultimos_concursos = self.estatisticas()
                    print("Números com menos aparições nos últimos concursos:")
                    for numero, concursos in ultimos_concursos.items():
                        print(f"Número {numero:02d} - Última aparição há {concursos} concursos")
                    input("Pressione Enter para continuar...")
                    system('cls')
                case "q":
                    print("Saindo do painel.\n")
                    break
                case _:
                    print("Opção inválida. Tente novamente.\n")
            
    
    def gerar_numeros(self):
        self._numeros = random.sample(range(self._numero_minimo, self._numero_maximo + 1), self._quantidade_num)
        with sqlite3.connect('loteria.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO jogos (numeros, jogo) VALUES (?, ?)', (str(sorted(self._numeros)),self.jogo))
            conn.commit()
        return self._numeros
    
    def ultimos_jogos_gerados(self, limite: int = 10):
        with sqlite3.connect('loteria.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT numeros, data_jogo FROM jogos WHERE jogo = ? ORDER BY data_jogo DESC LIMIT ?', (self.jogo, limite))
            jogos = cursor.fetchall()
            return jogos
    
class MegaSena(Jogo):
    def __init__(self, numeros = None, qtd_num = 6):
        super().__init__(numeros, 'megasena', qtd_num, num_max = 60, num_min = 1, qtd_max_num = 15, qtd_min_num = 6)
        
class LotoFacil(Jogo):
    def __init__(self, numeros = None, qtd_num = 15):
        super().__init__(numeros, 'lotofacil', qtd_num, num_max = 25, num_min = 1, qtd_max_num = 18, qtd_min_num = 15)
        
class Quina(Jogo):
    def __init__(self, numeros = None, qtd_num = 5):
        super().__init__(numeros, 'quina', qtd_num, num_max = 80, num_min = 1, qtd_max_num = 15, qtd_min_num = 5)
        
class DiaDeSorte(Jogo):
    def __init__(self, numeros = None, qtd_num = 7):
        super().__init__(numeros, 'diadesorte', qtd_num, num_max = 31, num_min = 1, qtd_max_num = 15, qtd_min_num = 7)
    
    
def resetar_sql():
    with sqlite3.connect('loteria.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM jogos')
        conn.commit()
    

def main():
    while True:
        user_input = input(
            f"""
            +======================================+
            |            Mega Senha Menu           |
            +======================================+
            |  [1] Mega Sena                       |
            |  [2] Loto Fácil                      |
            |  [3] Quina                           |
            |  [4] Dia de Sorte                    |
            |  [q] Sair                            |
            +--------------------------------------+
            > Escolha uma opção:
              """
            )
        system('cls')
        
        match user_input:
            case "1":
                megasena = MegaSena()
                megasena.painel()
            case "2":
                lotofacil = LotoFacil()
                lotofacil.painel()
            case "3":
                quina = Quina()
                quina.painel()
            case "4":
                diadesorte = DiaDeSorte()
                diadesorte.painel()
            case "q":
                print("Saindo do programa.")
                break
            case _:
                print("Opção inválida. Tente novamente.\n")
    

    
if __name__ == "__main__":
    main()