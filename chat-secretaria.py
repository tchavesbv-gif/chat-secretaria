from datetime import datetime, timedelta
import pytz
import streamlit as st
from supabase import create_client, Client

# Configuração da página do Streamlit com layout mais amplo para simular a janela de chat
st.set_page_config(page_title="Chat Clássico - Secretaria de Saúde", page_icon="🟢", layout="wide")

# Estilização CSS personalizada para dar o toque nostálgico (cores do MSN/ICQ e balões de mensagem)
st.markdown("""
    <style>
    .chat-container {
        background-color: #f4f6f9;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #d1d8e0;
    }
    .msg-box-user {
        background-color: #e3f2fd;
        padding: 10px 15px;
        border-radius: 12px 12px 2px 12px;
        margin-bottom: 10px;
        border-left: 4px solid #0078d7;
    }
    .msg-box-other {
        background-color: #ffffff;
        padding: 10px 15px;
        border-radius: 12px 12px 12px 2px;
        margin-bottom: 10px;
        border-left: 4px solid #7f8c8d;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# Inicialização da conexão com o Supabase utilizando os segredos
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# --- BARRA LATERAL (Estilo Lista de Contatos / Status do MSN) ---
with st.sidebar:
    st.markdown("### 🟢 Status do Usuário")
    status_atual = st.selectbox(
        "Meu Status:",
        ["🟢 Disponível", "🟡 Ocupado / Em atendimento", "🔴 Ausente", "⚪ Offline"]
    )
    
    st.markdown("---")
    st.markdown("### 🏥 Setores Conectados")
    st.markdown("- Recepção Central")
    st.markdown("- Regulação / TFD")
    st.markdown("- Farmácia Básica")
    st.markdown("- Vigilância em Saúde")
    st.markdown("- Gabinete / Gestão")
    st.markdown("---")
    st.info("💡 **Dica clássica:** Identifique-se com o seu Setor no campo ao lado para facilitar a comunicação da equipe!")

# --- TELA PRINCIPAL DO CHAT ---
st.title("💬 Chat Interno — Estilo Clássico (MSN / ICQ)")
st.write("---")

# Linha de identificação e status rápido
col_nome, col_vazio = st.columns([2, 3])
with col_nome:
    nome_setor = st.text_input("Seu Nome / Setor:", placeholder="Ex: João - Recepção", value="")

# Área de envio de mensagens compacta e organizada
with st.container():
    st.markdown("#### Escrever Mensagem")
    mensaje_col1, mensaje_col2 = st.columns([4, 1])
    
    with mensaje_col1:
        mensagem_texto = st.text_area("Mensagem:", placeholder="Digite seu recado aqui...", height=80, label_visibility="collapsed")
    
    with mensaje_col2:
        st.write("") # Espaçamento vertical
        st.write("")
        enviar_btn = st.button("Enviar 🚀", use_container_width=True)
    
    # Upload de arquivo opcional em expansor discreto
    with st.expander("📎 Anexar documento ou foto"):
        arquivo_upload = st.file_uploader("Escolher arquivo", type=["png", "jpg", "jpeg", "pdf", "docx"], label_visibility="collapsed")

    url_arquivo_upado = None
    tipo_arquivo_upado = None

    if enviar_btn:
        if nome_setor and (mensagem_texto or arquivo_upload):
            
            # Se houver arquivo anexado, faz o upload para o Storage do Supabase
            if arquivo_upload is not None:
                try:
                    file_bytes = arquivo_upload.getvalue()
                    file_name = f"{datetime.now().timestamp()}_{arquivo_upload.name}"
                    
                    supabase.storage.from_("chat-arquivos").upload(file_name, file_bytes)
                    url_res = supabase.storage.from_("chat-arquivos").get_public_url(file_name)
                    url_arquivo_upado = url_res
                    tipo_arquivo_upado = arquivo_upload.type
                except Exception as e:
                    st.error(f"Erro ao enviar o arquivo: {e}")

            # Captura a data e hora exata para o fuso horário do Brasil
            fuso_brasil = pytz.timezone('America/Sao_Paulo')
            data_hora_brasil = datetime.now(fuso_brasil).isoformat()

            # Monta o registro para inserção na tabela 'mensagens'
            novo_registro = {
                "remetente": f"{nome_setor} ({status_atual.split(' ')[0]})",
                "conteudo": mensagem_texto if mensagem_texto else "",
                "arquivo_url": url_arquivo_upado,
                "tipo_arquivo": tipo_arquivo_upado,
                "created_at": data_hora_brasil
            }

            try:
                supabase.table("mensagens").insert(novo_registro).execute()
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar mensagem no banco de dados: {e}")
        else:
            st.warning("Por favor, preencha o seu nome/setor e escreva uma mensagem ou anexe um arquivo.")

st.write("---")
st.subheader("📜 Histórico de Conversas da Secretaria")

# Bloco de listagem das mensagens em estilo de balões de chat
try:
    resposta = supabase.table("mensagens").select("*").order("created_at", desc=True).limit(50).execute()
    mensagens = resposta.data

    if mensagens:
        for msg in mensagens:
            remetente = msg.get("remetente", "Anônimo")
            conteudo = msg.get("conteudo", "")
            arquivo_url = msg.get("arquivo_url")
            tipo_arquivo = msg.get("tipo_arquivo")
            created_at_str = msg.get("created_at")

            # Formata a exibição da data e hora aplicando o ajuste de fuso
            if created_at_str:
                try:
                    limpo = created_at_str.replace("Z", "").split("+")[0]
                    dt_obj = datetime.fromisoformat(limpo)
                    dt_brasil = dt_obj - timedelta(hours=3)
                    hora_formatada = dt_brasil.strftime("%d/%m/%Y às %H:%M")
                except:
                    hora_formatada = created_at_str[:16].replace("T", " ")
            else:
                hora_formatada = ""

            # Renderiza o balão de mensagem estilizado
            with st.container():
                st.markdown(f"""
                    <div class="msg-box-other">
                        <b>{remetente}</b> <span style="color: gray; font-size: 0.85em;">({hora_formatada})</span><br>
                        <p style="margin-top: 5px; margin-bottom: 5px;">{conteudo}</p>
                    </div>
                """, unsafe_allow_html=True)

            # Exibe imagem ou link de documento caso tenha anexo
            if arquivo_url:
                if tipo_arquivo and "image" in tipo_arquivo:
                    st.image(arquivo_url, width=350)
                else:
                    st.markdown(f"📎 [Baixar / Ver Documento Anexado]({arquivo_url})")

            st.write("") # espaçamento leve entre as bolhas
    else:
        st.info("Ainda não há conversas registradas. Envie a primeira mensagem para iniciar o chat!")

except Exception as e:
    st.error(f"Erro ao carregar as mensagens: {e}")
