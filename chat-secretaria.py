from datetime import datetime, timedelta
import pytz
import streamlit as st
from supabase import create_client, Client

# Configuração da página do Streamlit
st.set_page_config(page_title="Chat Interno - Secretaria de Saúde", page_icon="💬", layout="wide")

# Estilização CSS avançada para destacar botões, inputs, blocos e balões de chat
st.markdown("""
    <style>
    /* Fundo geral e fontes */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Cabeçalho principal */
    h1 {
        color: #1e3d59;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Caixa lateral (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #f1f5f9;
        border-right: 1px solid #e2e8f0;
    }

    /* Estilização dos inputs e caixas de texto */
    .stTextInput input, .stTextArea textarea {
        background-color: #ffffff !important;
        border: 2px solid #cbd5e1 !important;
        border-radius: 8px !important;
        color: #1e293b !important;
        font-size: 15px !important;
        padding: 10px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #0078d7 !important;
        box-shadow: 0 0 0 3px rgba(0, 120, 215, 0.15) !important;
    }

    /* Botão de Enviar estilizado */
    .stButton button {
        background: linear-gradient(135deg, #0078d7 0%, #005a9e 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.2rem !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(0, 120, 215, 0.2) !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #005a9e 0%, #004578 100%) !important;
        box-shadow: 0 6px 8px rgba(0, 120, 215, 0.3) !important;
        transform: translateY(-1px);
    }

    /* Cartão do Mural de Mensagens (Estilo Balão de Chat) */
    .chat-bubble {
        background-color: #ffffff;
        padding: 16px 20px;
        border-radius: 12px;
        border-left: 5px solid #0078d7;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
        transition: transform 0.2s ease;
    }
    .chat-bubble:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
    }
    
    /* Detalhes do remetente e hora */
    .chat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 6px;
    }
    .chat-author {
        font-weight: 700;
        color: #1e3d59;
        font-size: 1.05rem;
    }
    .chat-time {
        color: #64748b;
        font-size: 0.85rem;
    }
    .chat-content {
        color: #334155;
        font-size: 1rem;
        line-height: 1.5;
        white-space: pre-wrap;
    }
    </style>
""", unsafe_allow_html=True)

# Inicialização da conexão com o Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# --- BARRA LATERAL (Status e Contatos) ---
with st.sidebar:
    st.markdown("### 🟢 Status do Operador")
    status_atual = st.selectbox(
        "Selecione o estado:",
        ["🟢 Disponível", "🟡 Ocupado em Atendimento", "🔴 Ausente", "⚪ Offline"]
    )
    
    st.markdown("---")
    st.markdown("### 🏥 Setores Integrados")
    st.markdown("• **Recepção Central**")
    st.markdown("• **Regulação e TFD**")
    st.markdown("• **Farmácia Básica**")
    st.markdown("• **Vigilância em Saúde**")
    st.markdown("• **Gabinete / Gestão**")
    st.markdown("---")
    st.info("💡 **Dica:** Insira o seu nome seguido do setor (Ex: *Ana - Farmácia*) para facilitar a identificação.")

# --- TELA PRINCIPAL ---
st.title("💬 Chat Interno — Secretaria de Saúde")
st.markdown("Painel de comunicação rápida e partilha de documentos entre setores.")
st.write("")

# Seção de Envio em Caixa Destacada
with st.container():
    st.markdown("#### ✍️ Nova Mensagem")
    
    col_input1, col_input2 = st.columns([1, 2])
    with col_input1:
        nome_setor = st.text_input("Seu Nome / Setor:", placeholder="Ex: João - Recepção")
    
    mensagem_texto = st.text_area("Mensagem:", placeholder="Escreva o seu recado, aviso ou instrução aqui...", height=100)
    
    col_file, col_btn = st.columns([3, 1])
    with col_file:
        arquivo_upload = st.file_uploader("Anexar imagem ou documento (Opcional)", type=["png", "jpg", "jpeg", "pdf", "docx"])
    
    with col_btn:
        st.write("") # Espaçamento alinhado
        st.write("")
        enviar_btn = st.button("Enviar Mensagem 🚀")

    url_arquivo_upado = None
    tipo_arquivo_upado = None

    if enviar_btn:
        if nome_setor and (mensagem_texto or arquivo_upload):
            
            # Upload para o Storage do Supabase se houver arquivo
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

            # Captura o horário exato ajustado para Brasília
            fuso_brasil = pytz.timezone('America/Sao_Paulo')
            data_hora_brasil = datetime.now(fuso_brasil).isoformat()

            novo_registro = {
                "remetente": f"{nome_setor} [{status_atual.split(' ')[0]}]",
                "conteudo": mensagem_texto if mensagem_texto else "",
                "arquivo_url": url_arquivo_upado,
                "tipo_arquivo": tipo_arquivo_upado,
                "created_at": data_hora_brasil
            }

            try:
                supabase.table("mensagens").insert(novo_registro).execute()
                st.success("Mensagem enviada com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar no banco de dados: {e}")
        else:
            st.warning("Preencha o seu nome/setor e escreva uma mensagem ou anexe um ficheiro.")

st.markdown("---")
st.subheader("📜 Mural de Mensagens e Avisos")

# Listagem estilizada das mensagens
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

            # Formatação exata do horário de Brasília
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

            # Renderização em balão moderno
            st.markdown(f"""
                <div class="chat-bubble">
                    <div class="chat-header">
                        <span class="chat-author">👤 {remetente}</span>
                        <span class="chat-time">🕒 {hora_formatada}</span>
                    </div>
                    <div class="chat-content">{conteudo}</div>
                </div>
            """, unsafe_allow_html=True)

            # Exibe imagem ou ficheiro anexado com destaque
            if arquivo_url:
                if tipo_arquivo and "image" in tipo_arquivo:
                    st.image(arquivo_url, width=400)
                else:
                    st.markdown(f"📎 **[Descarregar / Visualizar Documento Anexado]({arquivo_url})**")

            st.write("") # Espaçamento leve
    else:
        st.info("Ainda não existem mensagens registadas no mural. Seja o primeiro a interagir!")

except Exception as e:
    st.error(f"Erro ao carregar o mural: {e}")
