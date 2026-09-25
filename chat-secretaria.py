import os
import streamlit as st
from supabase import create_client, Client

# Pega as chaves de forma segura das Configurações do Streamlit Cloud
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(URL, KEY)

st.title("💬 Chat Interno - Secretaria de Saúde")

# Identificação do colaborador
remetente = st.text_input("Seu Nome / Setor:", placeholder="Ex: João - Recepção")

# Formulário de Envio
with st.form("form_chat", clear_on_submit=True):
    conteudo = st.text_area("Digite sua mensagem:")
    arquivo_enviado = st.file_uploader("Enviar foto ou documento", type=["png", "jpg", "jpeg", "pdf", "docx"])
    
    enviar = st.form_submit_button("Enviar Mensagem")

    if enviar:
        if not remetente:
            st.warning("Por favor, informe seu nome ou setor antes de enviar.")
        elif not conteudo and not arquivo_enviado:
            st.warning("Escreva uma mensagem ou anexe um arquivo.")
        else:
            arquivo_url = None
            tipo_arquivo = "texto"
            
            # Se houver arquivo, faz o upload para o Storage do Supabase
            if arquivo_enviado:
                nome_arquivo = arquivo_enviado.name
                if nome_arquivo.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    tipo_arquivo = "imagem"
                else:
                    tipo_arquivo = "documento"
                
                path_no_bucket = f"uploads/{nome_arquivo}"
                supabase.storage.from_("chat-arquivos").upload(path_no_bucket, arquivo_enviado.getvalue(), file_options={"upsert": "true"})
                
                arquivo_url = supabase.storage.from_("chat-arquivos").get_public_url(path_no_bucket)

            # Salva na tabela do banco
            supabase.table("mensagens").insert({
                "remetente": remetente,
                "conteudo": conteudo,
                "arquivo_url": arquivo_url,
                "tipo_arquivo": tipo_arquivo
            }).execute()
            
            st.success("Mensagem enviada!")
            st.rerun()

st.divider()

# Histórico de Conversas
st.subheader("Mural de Mensagens")

resposta = supabase.table("mensagens").select("*").order("created_at", desc=True).limit(50).execute()
mensagens = resposta.data

for msg in mensagens:
    st.markdown(f"**{msg['remetente']}** *({msg['created_at'][11:16]})*:")
    if msg['conteudo']:
        st.write(msg['conteudo'])
        
    if msg['arquivo_url']:
        if msg['tipo_arquivo'] == 'imagem':
            st.image(msg['arquivo_url'], width=300)
        else:
            st.markdown(f"📁 [Baixar Documento Anexado]({msg['arquivo_url']})")
    st.markdown("---")