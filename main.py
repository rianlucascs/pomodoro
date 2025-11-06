
from os.path import join, dirname, abspath, exists
from os import listdir, remove
import numpy as np
from scipy.io.wavfile import write
from datetime import date, datetime
import winsound
import sqlite3
from pandas import read_sql_query, to_datetime
import streamlit as st
import altair as alt
from time import sleep
import threading


__python__ = 3.10

class Sound:
    """
    Classe responsável por criar e reproduzir um som de ruído branco.
    """

    def __init__(self, path, duracao):
        """
        Inicializa o objeto e garante que o arquivo de som exista.
        """
        self.path = path
        self.duracao = duracao
        self.path_sound = join(path, f"ruido_branco_{duracao}.wav")
        self._create_sound()

    def _create_sound(self):
        """
        Cria o arquivo de ruído branco caso ele ainda não exista.
        """
        if not exists(self.path_sound):

            # Verifica se existem outros arquivos de som diferente do selecionado            
            for file in listdir(self.path):
                if file.endswith(".wav"):
                    remove(join(self.path, file))
                    break
            print(f"\nArquivo '{file}' removido com sucesso!")

        if not exists(self.path_sound):
            duration = self.duracao * 60  
            sample_rate = 44100
            noise = np.random.normal(0, 1, int(sample_rate * duration))
            noise = noise / np.max(np.abs(noise)) * 0.3 
            write(self.path_sound, sample_rate, noise.astype(np.float32))
            print(f"\nArquivo WAV 'ruido_branco{self.duracao}.wav' criado com sucesso!")
    
    
    def start_sound(self):
        """
        Inicia a reprodução do som.
        """
        # winsound.PlaySound(self.path_sound, winsound.SND_FILENAME)
        thread = threading.Thread(
            target=winsound.PlaySound,
            args=(self.path_sound, winsound.SND_FILENAME)
        )
        thread.start()

class Data:
    """
    Classe responsável por manipular o banco de dados das atividades.
    """

    def __init__(self, path):
        """
        Define o caminho e cria a tabela referente ao mês e ano atuais.
        """
        self.path = path
        self._table_name = f"table_{date.today().month}_{date.today().year}"
        self.path_db = join(self.path, "data.db")
        self._create_table() 

    def _connect(self):
        """
        Cria e retorna uma conexão com o banco de dados SQLite.
        """
        return sqlite3.connect(self.path_db)

    def _create_table(self):
        """
        Cria a tabela para armazenar tarefas caso ainda não exista.
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                DATA TEXT NOT NULL,
                NOME_ATIVIDADE TEXT NOT NULL,
                HORA_INICIO TEXT NOT NULL,
                DURACAO TEXT NOT NULL
            );
        """)
        conn.commit()
        conn.close()
    
    def load_data(self):
        conn = self._connect()
        df = read_sql_query(f"SELECT * FROM {self._table_name}", conn)
        conn.close()
        return df
    
    def delete_task(self, task_id):
        """
        Remove uma atividade pelo ID.
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {self._table_name} WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        

    def add_task(self, dict_task):
        """
        Adiciona uma nova tarefa no banco de dados.
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(f"""
                    INSERT INTO {self._table_name} (
                    DATA, NOME_ATIVIDADE, HORA_INICIO, DURACAO)
                    VALUES (?, ?, ?, ?)
        """, (
            dict_task["DATA"],
            dict_task["NOME_ATIVIDADE"],
            dict_task["HORA_INICIO"],
            dict_task["DURACAO"]
        ))
        conn.commit()
        conn.close()
    
class App:
    """
    Classe responsável por gerenciar e exibir a interface do dashboard de produtividade.
    """

    def __init__(self, path):
        """
        Inicializa o aplicativo conectando o banco de dados e carregando os registros existentes.
        """
        self.path = path
        self.data = Data(self.path)

        self.df = self.data.load_data()
        self.df["DATA"] = self.df["DATA"] = to_datetime(self.df["DATA"])

    def _title(self):
        """
        Configura o layout da página e exibe o título principal do dashboard.
        """
        st.set_page_config(page_title="Dashboard Pomodoro", page_icon="⏱", layout="wide")
        st_autorefresh = st.experimental_rerun if False else None
        # Atualiza automaticamente a cada 10 segundos
        st_autorefresh = st.sidebar.button("Atualizar agora")
        st.title("Dashboard de Produtividade - Pomodoro")

    def _cards_KPI(self):
        """
        Exibe indicadores simples de produtividade, como o total de sessões registradas.
        """
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Sessões", len(self.df))
        with col2:
            minutos = sum(self.df['DURACAO'].astype(int))
            horas = minutos // 60
            minutos_restantes = minutos % 60
            st.metric("Total de Horas", f"{horas:02d}:{minutos_restantes:02d}")

        st.markdown("---")
    
    # XXX ###
    def _table_1(self):
        """
        Exibe uma tabela com os registros do mês atual.
        """
        st.subheader("Registros do mês")
        st.dataframe(self.df, width='stretch')

    # XXX ###
    def _table_2(self):
        st.subheader("Registros do mês")

        # Mostrar tabela com opção de deletar
        for idx, row in self.df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 3, 3, 3, 1])
            col1.write(row["id"])
            col2.write(row["DATA"])
            col3.write(row["NOME_ATIVIDADE"])
            col4.write(f"{row['DURACAO']} min")

            if col5.button("🗑️", key=f"del_{row['id']}"):
                self.data.delete_task(row["id"])
                st.toast("Registro removido com sucesso ✅")
                st.rerun()

    def _table(self):
        st.subheader("Registros do mês")

        df = self.df.copy()
        df["Excluir"] = False  # checkbox para deletar

        edited_df = st.data_editor(
            df,
            hide_index=True,
            column_config={
                "Excluir": st.column_config.CheckboxColumn(
                    help="Selecione para remover",
                    default=False
                )
            },
            width="stretch"
        )

        # Verifica linhas marcadas
        excluidos = edited_df[edited_df["Excluir"] == True]

        if len(excluidos) > 0:
            if st.button("🗑️ Remover Selecionados"):
                for task_id in excluidos["id"].tolist():
                    self.data.delete_task(task_id)

                st.success("Registros removidos com sucesso ✅")
                st.rerun()


    def _grafico_sessao_por_dia(self):
        """
        Gera um gráfico mostrando a quantidade de sessões realizadas por dia.
        """
        st.subheader("Sessões por dia")
        df_day = self.df.copy()
        df_day["DATA"] = df_day["DATA"].dt.date
        chart2 = (
            alt.Chart(df_day)
            .mark_line(point=True)
            .encode(
                x="DATA:T",
                y="count(id):Q",
                tooltip=["count(id)"]
            )
        )
        st.altair_chart(chart2, width='stretch')

    def _formulario_para_adicionar_nova_sessao(self):
        """
        Exibe um formulário para adicionar uma nova sessão e registra os dados no banco.
        """
        hora_inicio = datetime.now().strftime('%H:%M:%S')
        st.subheader("Adicionar Nova Sessão")
        with st.form("add_session_form"):
            atividade = st.text_input("Nome da Atividade")
            st.text_input("Hora de Início", value=hora_inicio, disabled=True)
            duracao = st.number_input("Duração (minutos)", min_value=1, max_value=240, value=25)
            submit = st.form_submit_button("Salvar Sessão")


        if submit and atividade:
            self.data.add_task({
                "DATA": date.today(),
                "NOME_ATIVIDADE": atividade,
                "HORA_INICIO": hora_inicio,
                "DURACAO": duracao
            }
            )

            st.toast("✅ Sessão iniciada! Bom foco! 🚀")

            # Toca o som ao iniciar a sessão
            sound = Sound(self.path, duracao)
            sound.start_sound()

            # Barra de progresso
            st.subheader("Progresso da Sessão")
            st.toast("🎧")
            progress_bar = st.progress(0)
            tempo_total = duracao * 60 

            for t in range(tempo_total):
                progress = int(( (t+1) / tempo_total) * 100)
                progress_bar.progress(progress)
                sleep(1) 

            st.success("Sessão adicionada com sucesso!")

    def run(self):
        """
        Executa o fluxo principal da aplicação, exibindo a interface completa.
        """
        self._title()
        self._cards_KPI()
        self._table()
        self._grafico_sessao_por_dia()
        self._formulario_para_adicionar_nova_sessao()


if __name__ == "__main__":
    path = dirname(abspath(__file__))
    app = App(path)
    app.run()

