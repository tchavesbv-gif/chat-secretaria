from datetime import datetime
import pytz
import streamlit as st
from supabase import create_client, Client

# Configuração da página do Streamlit
st.set_page_config(page_title="Chat Interno - Secretaria de Saúde", page_icon="💬", layout="centered")

# Inicialização da conexão com o Supabase utilizando os segredos
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

st.title("💬 Chat Interno - Secretaria de Saúde")
st.write("---")

# Campo para o nome ou setor do usuário
nome_setor = st.text_input("Seu Nome / Setor:", placeholder="Ex: João - Recepção")

# Área de envio de mensagens
with st.container():
    mensagem_texto = st.text_area("Digite sua mensagem:", placeholder="Escreva seu recado aqui...")
    
    # Upload de arquivo ou foto opcional
    arquivo_upload = st.file_uploader("Enviar foto ou documento", type=["png", "jpg", "jpeg", "pdf", "docx"])
    
    url_arquivo_upado = None
    tipo_arquivo_upado = None

    if st.button("Enviar Mensagem"):
        if nome_setor and (mensagem_texto or arquivo_upload):
            
            # Se houver arquivo anexado, faz o upload para o Storage do Supabase
            if arquivo_upload is not None:
                try:
                    file_bytes = arquivo_upload.getvalue()
                    file_name = f"{datetime.now().timestamp()}_{arquivo_upload.name}"
                    
                    # Faz o upload para o bucket 'chat-arquivos'
                    supabase.storage.from_("chat-arquivos").upload(file_name, file_bytes)
                    
                    # Obtém a URL pública do arquivo
                    url_res = supabase.storage.from_("chat-arquivos").get_public_url(file_name)
                    url_arquivo_upado = url_res
                    tipo_arquivo_upado = arquivo_upload.type
                except Exception as e:
                    st.error(f"Erro ao enviar o arquivo: {e}")

            # Captura a data e hora ajustada rigorosamente para o fuso horário do Brasil
            fuso_brasil = pytz.timezone('America/Sao_Paulo')
            data_hora_brasil = datetime.now(fuso_brasil).isoformat()

            # Monta o registro para inserção na tabela 'mensagens'
            novo_registro = {
                "remetente": nome_setor,
                "conteudo": mensagem_texto if mensagem_texto else "",
                "arquivo_url": url_arquivo_upado,
                "tipo_arquivo": tipo_arquivo_upado,
                "created_at": data_hora_brasil
            }

            try:
                # Insere os dados na tabela do Supabase
                supabase.table("mensagens").insert(novo_registro).execute()
                st.success("Mensagem enviada com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar mensagem no banco de dados: {e}")
        else:
            st.warning("Por favor, preencha o seu nome/setor e escreva uma mensagem ou anexe um arquivo.")

st.write("---")
st.subheader("Mural de Mensagens")

# Bloco de listagem das mensagens do mural ordenadas da mais recente para a mais antiga
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

            # Formata a exibição amigável da data e hora vindas do banco
            if created_at_str:
                try:
                    dt_obj = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    hora_formatada = dt_obj.strftime("%d/%m/%Y às %H:%M")
                except:
                    hora_formatada = created_at_str[:16].replace("T", " ")
            else:
                hora_formatada = ""

            # Exibe o card de cada mensagem no mural
            st.markdown(f"**{remetente}** *({hora_formatada})*:")
            if conteudo:
                st.write(conteudo)

            # Exibe imagem ou link de documento caso tenha anexo
            if arquivo_url:
                if tipo_arquivo and "image" in tipo_arquivo:
                    st.image(arquivo_url, width=400)
                else:
                    st.markdown(f"📎 [Baixar / Ver Documento Anexado]({arquivo_url})")

            st.write("---")
    else:
        st.info("Nenhuma mensagem no mural ainda. Seja o primeiro a enviar!")

except Exception as e:
    st.error(f"Erro ao carregar o mural de mensagens: {e}")
