# EXPLICAÇÕES DAS SEÇÕES
EXPLICACOES = {
    "1 - IMPORTS E CONFIGURAÇÃO": (
        "Importa as bibliotecas e configura a página do Streamlit. "
        "O zxing-cpp será usado para ler QR Codes; o Pillow abre e trata imagens."
    ),
    "2 - FUNÇÕES": (
        "A função gerar_qr cria a imagem e os dados PNG, podendo incluir uma logo. "
        "A função ler_qr envia a imagem ao zxing-cpp e devolve os textos encontrados."
    ),
    "3 - ABAS E GERAÇÃO": (
        "Cria as abas e os controles para personalizar o QR Code. "
        "Ao clicar em Gerar, valida o texto, cria a imagem e oferece o download."
    ),
    "4 - LEITURA DE QR CODE": (
        "Recebe uma imagem, mostra uma prévia e tenta ler os QR Codes nela. "
        "Se encontrar um endereço web, também exibe um botão para abri-lo."
    ),
    "5 - EXPLICAÇÃO DO CÓDIGO": (
        "Lê este arquivo e procura os marcadores de seção. Para cada marcador, "
        "recorta o código até o próximo e mostra esse trecho junto da explicação."
    ),
}


# ===== 1 - IMPORTS E CONFIGURAÇÃO =====
import io
import re
from pathlib import Path

import qrcode
import streamlit as st
import zxingcpp
from PIL import Image


st.set_page_config(
    page_title="QR Studio",
    page_icon="🔳",
)

st.title("🔳 QR Studio")
st.caption("Gere e leia QR Codes.")


# ===== 2 - FUNÇÕES =====
def gerar_qr(texto, cor, fundo, tamanho, margem, correcao, logo=None):
    """Gera um QR Code e devolve a imagem e o arquivo PNG."""
    qr = qrcode.QRCode(
        box_size=tamanho,
        border=margem,
        error_correction=correcao,
    )
    qr.add_data(texto)
    qr.make(fit=True)

    imagem = qr.make_image(
        fill_color=cor,
        back_color=fundo,
    ).convert("RGB")

    if logo is not None:
        imagem_logo = Image.open(logo).convert("RGBA")
        imagem_logo.thumbnail((imagem.width // 5, imagem.height // 5))

        x = (imagem.width - imagem_logo.width) // 2
        y = (imagem.height - imagem_logo.height) // 2
        imagem.paste(imagem_logo, (x, y), imagem_logo)

    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG")

    return imagem, buffer.getvalue()


def ler_qr(imagem):
    """Lê os QR Codes encontrados na imagem."""
    codigos = zxingcpp.read_barcodes(
        imagem.convert("RGB"),
        formats=zxingcpp.BarcodeFormat.QRCode,
    )

    return [codigo.text for codigo in codigos if codigo.text]


# ===== 3 - ABAS E GERAÇÃO =====
aba_gerar, aba_ler, aba_explicacao = st.tabs(
    ["Gerar QR Code", "Ler QR Code", "Explicação"]
)

with aba_gerar:
    texto = st.text_area("Texto ou link")

    coluna1, coluna2 = st.columns(2)

    with coluna1:
        cor = st.color_picker("Cor do QR Code", "#111111")
        tamanho = st.slider("Tamanho", 5, 20, 10)

    with coluna2:
        fundo = st.color_picker("Cor de fundo", "#FFFFFF")
        margem = st.slider("Margem", 1, 10, 4)

    nivel = st.selectbox(
        "Correção de erros",
        ["Baixa", "Média", "Alta", "Máxima"],
        index=2,
    )

    logo = st.file_uploader(
        "Logo opcional",
        type=["png", "jpg", "jpeg"],
    )

    niveis = {
        "Baixa": qrcode.constants.ERROR_CORRECT_L,
        "Média": qrcode.constants.ERROR_CORRECT_M,
        "Alta": qrcode.constants.ERROR_CORRECT_Q,
        "Máxima": qrcode.constants.ERROR_CORRECT_H,
    }

    if st.button("Gerar", type="primary"):
        if not texto.strip():
            st.warning("Digite um texto ou link.")
        else:
            imagem, png = gerar_qr(
                texto=texto.strip(),
                cor=cor,
                fundo=fundo,
                tamanho=tamanho,
                margem=margem,
                correcao=niveis[nivel],
                logo=logo,
            )

            st.image(imagem, width=300)
            st.download_button(
                "Baixar PNG",
                data=png,
                file_name="qr-code.png",
                mime="image/png",
            )


# ===== 4 - LEITURA DE QR CODE =====
with aba_ler:
    arquivo = st.file_uploader(
        "Envie uma imagem com QR Code",
        type=["png", "jpg", "jpeg"],
    )

    if arquivo is not None:
        imagem = Image.open(arquivo).convert("RGB")
        st.image(imagem, width=300)

        resultados = ler_qr(imagem)

        if resultados:
            for numero, resultado in enumerate(resultados, start=1):
                st.text_area(
                    f"Resultado {numero}",
                    value=resultado,
                    key=f"resultado_{numero}",
                )

                if resultado.startswith(("http://", "https://")):
                    st.link_button(
                        f"Abrir link {numero}",
                        resultado,
                        key=f"link_{numero}",
                    )
        else:
            st.warning(
                "QR Code não encontrado. Tente uma imagem mais nítida e sem cortes."
            )


# ===== 5 - EXPLICAÇÃO DO CÓDIGO =====
with aba_explicacao:
    st.subheader("Explicação do código")

    try:
        fonte = Path(__file__).read_text(encoding="utf-8")

        marcadores = list(
            re.finditer(
                r"^# ===== (.+?) =====\s*$",
                fonte,
                flags=re.MULTILINE,
            )
        )

        for indice, marcador in enumerate(marcadores):
            titulo = marcador.group(1)

            inicio = marcador.end()
            fim = (
                marcadores[indice + 1].start()
                if indice + 1 < len(marcadores)
                else len(fonte)
            )

            trecho = fonte[inicio:fim].strip()

            with st.expander(titulo):
                st.write(EXPLICACOES.get(titulo, "Explicação não cadastrada."))
                st.code(trecho, language="python")

    except Exception as erro:
        st.error(f"Não foi possível ler o arquivo app.py: {erro}")
