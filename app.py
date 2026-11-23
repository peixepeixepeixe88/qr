import datetime
import inspect
import re

import bcrypt
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Atlantis", page_icon="🎮", layout="wide")

COLUNAS = ["nome", "criador", "descricao", "genero", "plataforma", "link", "capa", "data"]
ABA = "Jogos"
GENEROS = ["Ação", "Aventura", "Puzzle", "Terror", "RPG", "Corrida", "Esporte", "Outro"]
PLATAFORMAS = ["PC", "Android", "Navegador", "Outra"]


# ---------------------------------------------------------------
# 1. BANCO DE DADOS (planilha do Google Sheets)
# ---------------------------------------------------------------
def conexao():
    return st.connection("gsheets", type=GSheetsConnection)


def listar_jogos():
    try:
        df = conexao().read(worksheet=ABA, ttl=0)
    except Exception:
        st.warning("Não foi possível ler a planilha. Verifique os secrets.")
        return pd.DataFrame(columns=COLUNAS)

    df = df.dropna(how="all")
    for coluna in COLUNAS:
        if coluna not in df.columns:
            df[coluna] = ""
    return df[COLUNAS].fillna("")


def adicionar_jogo(registro: dict):
    df = listar_jogos()
    novo = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
    conexao().update(worksheet=ABA, data=novo)


# ---------------------------------------------------------------
# 2. PESQUISA E FILTROS
# ---------------------------------------------------------------
def filtrar_jogos(df, busca, genero):
    resultado = df.copy()
    if busca:
        resultado = resultado[resultado["nome"].str.contains(busca, case=False, na=False)]
    if genero != "Todos":
        resultado = resultado[resultado["genero"] == genero]
    return resultado


# ---------------------------------------------------------------
# 3. VALIDAÇÃO DO LINK
# ---------------------------------------------------------------
def validar_link(link):
    return bool(re.match(r"^https?://\S+$", link))


# ---------------------------------------------------------------
# 4. LOGIN (senha guardada como hash)
# ---------------------------------------------------------------
def exigir_login():
    if st.session_state.get("logado"):
        with st.sidebar:
            st.write(f"Logado como **{st.session_state['usuario']}**")
            if st.button("Sair"):
                st.session_state.clear()
                st.rerun()
        return True

    st.subheader("Entre para publicar um jogo")
    with st.form("form_login"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        hash_salvo = st.secrets.get("usuarios", {}).get(usuario)
        if hash_salvo and bcrypt.checkpw(senha.encode(), hash_salvo.encode()):
            st.session_state["logado"] = True
            st.session_state["usuario"] = usuario
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    return False


# ---------------------------------------------------------------
# PÁGINAS
# ---------------------------------------------------------------
def pagina_pesquisar():
    st.title("🎮 Atlantis")
    st.caption("Pesquise jogos anunciados pela comunidade. O site só indica o link, o jogo fica no endereço do criador.")

    df = listar_jogos()

    col1, col2 = st.columns([3, 2])
    busca = col1.text_input("Buscar pelo nome")
    generos = sorted([g for g in df["genero"].unique() if g])
    genero = col2.selectbox("Gênero", ["Todos"] + generos)

    resultado = filtrar_jogos(df, busca, genero)
    st.write(f"**{len(resultado)}** jogo(s) encontrado(s)")

    if resultado.empty:
        st.info("Nenhum jogo encontrado. Que tal ser o primeiro a anunciar?")

    colunas = st.columns(3)
    for i, (_, jogo) in enumerate(resultado.iterrows()):
        with colunas[i % 3]:
            with st.container(border=True):
                if str(jogo["capa"]).startswith("http"):
                    try:
                        st.image(jogo["capa"], use_container_width=True)
                    except Exception:
                        pass
                st.subheader(jogo["nome"])
                st.caption(f"{jogo['genero']} • {jogo['plataforma']} • por {jogo['criador']}")
                st.write(jogo["descricao"])
                st.link_button("Ver jogo", jogo["link"])


def pagina_anunciar():
    st.title("📢 Anunciar jogo")

    if not exigir_login():
        st.stop()

    with st.form("form_anuncio", clear_on_submit=True):
        nome = st.text_input("Nome do jogo *")
        criador = st.text_input("Nome do criador *", value=st.session_state["usuario"])
        descricao = st.text_area("Descrição curta *", max_chars=200)
        genero = st.selectbox("Gênero", GENEROS)
        plataforma = st.selectbox("Plataforma", PLATAFORMAS)
        link = st.text_input("Link do jogo * (começando com https://)")
        capa = st.text_input("Link de uma imagem de capa (opcional)")
        publicar = st.form_submit_button("Publicar")

    if publicar:
        if not nome or not criador or not descricao or not link:
            st.error("Preencha todos os campos obrigatórios (*).")
        elif not validar_link(link):
            st.error("O link precisa começar com http:// ou https://")
        else:
            adicionar_jogo({
                "nome": nome,
                "criador": criador,
                "descricao": descricao,
                "genero": genero,
                "plataforma": plataforma,
                "link": link,
                "capa": capa,
                "data": datetime.date.today().isoformat(),
            })
            st.success("Jogo publicado! Veja ele na aba Pesquisar.")


def pagina_apresentacao():
    st.title("ℹ️ Apresentação do Atlantis")
    st.write("Cada tópico explica uma parte do projeto e mostra o trecho de código que a faz funcionar.")

    topicos = [
        (
            "1- O que é o Atlantis",
            "Um catálogo de jogos. Criadores cadastram o nome, a descrição e o link do jogo, e qualquer pessoa pode pesquisar. O site não hospeda o jogo, ele só indica onde ele está.",
            None,
        ),
        (
            "2- Banco de dados em planilha",
            "Cada linha da planilha é um jogo. `listar_jogos` lê a planilha em tempo real (`ttl=0`) e `adicionar_jogo` junta o novo jogo à tabela e grava de volta.",
            [listar_jogos, adicionar_jogo],
        ),
        (
            "3- Pesquisa e filtros",
            "`filtrar_jogos` aplica a busca pelo nome, sem diferenciar maiúsculas, e depois o filtro de gênero. Os resultados aparecem em cards na página Pesquisar.",
            [filtrar_jogos],
        ),
        (
            "4- Validação do link",
            "`validar_link` usa uma expressão regular para garantir que o link começa com http:// ou https:// e não tem espaços. Evita anúncios com links quebrados.",
            [validar_link],
        ),
        (
            "5- Login só para publicar",
            "`exigir_login` compara a senha digitada com um hash `bcrypt` guardado nos secrets. A senha nunca fica escrita no código. Quem não está logado vê apenas o formulário de entrada.",
            [exigir_login],
        ),
        (
            "6- Página de anúncio",
            "`pagina_anunciar` chama o login primeiro (`st.stop()` interrompe a página se não houver login), depois mostra o formulário e publica o jogo.",
            [pagina_anunciar],
        ),
        (
            "7- Hospedagem",
            "O código fica no GitHub e é publicado no Streamlit Community Cloud. Cada alteração no GitHub atualiza o site automaticamente.",
            None,
        ),
    ]

    for titulo, explicacao, funcoes in topicos:
        st.markdown(f"### {titulo}")
        st.write(explicacao)
        if funcoes:
            for funcao in funcoes:
                st.code(inspect.getsource(funcao), language="python")
        st.markdown("---")


# ---------------------------------------------------------------
# MENU PRINCIPAL
# ---------------------------------------------------------------
def main():
    paginas = {
        "Pesquisar": pagina_pesquisar,
        "Anunciar jogo": pagina_anunciar,
        "Apresentação": pagina_apresentacao,
    }
    escolha = st.sidebar.radio("Menu", list(paginas.keys()))
    paginas[escolha]()


main()

