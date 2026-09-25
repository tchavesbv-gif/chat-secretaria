from datetime import datetime
import pytz

# No momento em que o usuário clica em "Enviar Mensagem":
if st.button("Enviar Mensagem"):
    if nome_setor and mensagem_texto:
        # Pega a data e hora atual ajustada para o fuso de Brasília
fuso_brasil = pytz.timezone('America/Sao_Paulo')
data_hora_brasil = datetime.now(fuso_brasil).isoformat()

        # Dados a serem enviados para o Supabase
        novo_registro = {
            "remetente": nome_setor,
            "conteudo": mensagem_texto,
            "arquivo_url": url_arquivo_upado, # (mantenha sua variável de arquivo aqui)
            "tipo_arquivo": tipo_arquivo_upado, # (mantenha sua variável de tipo aqui)
            "created_at": data_hora_brasil
        }

        # Insere na tabela explicitamente com o horário correto
        supabase.table("mensagens").insert(novo_registro).execute()
        st.success("Mensagem enviada com sucesso!")
        st.rerun()
