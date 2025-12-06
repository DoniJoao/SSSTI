import json
import boto3
import base64
import uuid
from datetime import datetime
from decimal import Decimal

# Inicializa clientes AWS
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
sns = boto3.client('sns')

# Configurações (VOCÊ VAI PREENCHER DEPOIS)
DYNAMODB_TABLE = 'TicketsSuporte'  # Nome da sua tabela
S3_BUCKET = 'suporte-ti-arquivos'  # Nome do seu bucket
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:XXXXX:NotificacaoSuporte'  # ARN do seu tópico SNS

def lambda_handler(event, context):
    """
    Função principal que processa solicitações de suporte
    """
    
    print("========== INÍCIO DA EXECUÇÃO ==========")
    print(f"Evento recebido: {json.dumps(event)}")
    print(f"Tipo do evento: {type(event)}")
    
    try:
        # Parse do body (vem do API Gateway)
        print("========== PARSE DO BODY ==========")
        if 'body' in event:
            print("Body encontrado no event")
            body = json.loads(event['body'])
        else:
            print("Body NÃO encontrado, usando event direto")
            body = event
        
        print(f"Body processado: {json.dumps(body)}")
        
        # Validação básica dos campos obrigatórios
        print("========== VALIDAÇÃO DE CAMPOS ==========")
        campos_obrigatorios = ['nome', 'email', 'telefone', 'tipoProblema', 'descricao']
        for campo in campos_obrigatorios:
            if campo not in body or not body[campo]:
                print(f"ERRO: Campo obrigatório ausente: {campo}")
                return resposta_erro(f"Campo obrigatório ausente: {campo}", 400)
        
        # Gera ID único para o ticket
        ticket_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        print(f"========== TICKET CRIADO ==========")
        print(f"Ticket ID: {ticket_id}")
        print(f"Timestamp: {timestamp}")
        
        # Processa arquivo se existir
        arquivo_url = None
        if 'arquivo' in body and body['arquivo']:
            arquivo_url = processar_arquivo(
                ticket_id, 
                body['arquivo']
            )
        
        # Prepara dados para o DynamoDB
        ticket_data = {
            'ticketId': ticket_id,
            'nome': body['nome'],
            'email': body['email'],
            'telefone': body['telefone'],
            'empresa': body.get('empresa', ''),
            'tipoProblema': body['tipoProblema'],
            'descricao': body['descricao'],
            'arquivoUrl': arquivo_url or '',
            'status': 'NOVO',
            'criadoEm': timestamp,
            'atualizadoEm': timestamp
        }
        
        # Salva no DynamoDB
        salvar_ticket(ticket_data)
        
        # Envia notificação por email
        enviar_notificacao(ticket_data)
        
        # Retorna sucesso
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',  # CORS
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'mensagem': 'Solicitação recebida com sucesso!',
                'ticketId': ticket_id,
                'status': 'processado'
            })
        }
        
    except Exception as e:
        print(f"Erro ao processar solicitação: {str(e)}")
        return resposta_erro(f"Erro interno: {str(e)}", 500)


def processar_arquivo(ticket_id, arquivo_data):
    """
    Faz upload do arquivo para o S3 e retorna a URL
    """
    try:
        arquivo_nome = arquivo_data['nome']
        arquivo_tipo = arquivo_data['tipo']
        arquivo_conteudo = arquivo_data['conteudo']
        
        # Decodifica base64
        arquivo_bytes = base64.b64decode(arquivo_conteudo)
        
        # Define o caminho no S3
        s3_key = f"tickets/{ticket_id}/{arquivo_nome}"
        
        # Upload para S3
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=arquivo_bytes,
            ContentType=arquivo_tipo,
            Metadata={
                'ticket-id': ticket_id,
                'uploaded-at': datetime.now().isoformat()
            }
        )
        
        # Retorna a URL do arquivo
        arquivo_url = f"s3://{S3_BUCKET}/{s3_key}"
        print(f"Arquivo salvo: {arquivo_url}")
        
        return arquivo_url
        
    except Exception as e:
        print(f"Erro ao processar arquivo: {str(e)}")
        return None


def salvar_ticket(ticket_data):
    """
    Salva o ticket no DynamoDB
    """
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        table.put_item(Item=ticket_data)
        print(f"Ticket salvo no DynamoDB: {ticket_data['ticketId']}")
        
    except Exception as e:
        print(f"Erro ao salvar no DynamoDB: {str(e)}")
        raise


def enviar_notificacao(ticket_data):
    """
    Envia notificação por email via SNS
    """
    try:
        # Monta a mensagem do email
        mensagem = f"""
Nova Solicitação de Suporte Recebida!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 DADOS DO CLIENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 Nome: {ticket_data['nome']}
📧 Email: {ticket_data['email']}
📱 Telefone: {ticket_data['telefone']}
🏢 Empresa: {ticket_data['empresa'] or 'Não informado'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 DETALHES DO PROBLEMA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️  Tipo: {ticket_data['tipoProblema']}
📝 Descrição:
{ticket_data['descricao']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📎 ANEXO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{ticket_data['arquivoUrl'] or 'Nenhum arquivo anexado'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔖 INFORMAÇÕES DO TICKET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ID do Ticket: {ticket_data['ticketId']}
Status: {ticket_data['status']}
Data/Hora: {ticket_data['criadoEm']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ Entre em contato com o cliente o mais breve possível!
        """
        
        # Publica no SNS
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f'🎫 Novo Ticket #{ticket_data["ticketId"][:8]} - {ticket_data["tipoProblema"]}',
            Message=mensagem
        )
        
        print(f"Notificação enviada via SNS")
        
    except Exception as e:
        print(f"Erro ao enviar notificação SNS: {str(e)}")
        # Não falha a função se o email não for enviado
        pass


def resposta_erro(mensagem, status_code):
    """
    Retorna uma resposta de erro padronizada
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': json.dumps({
            'erro': mensagem,
            'status': 'erro'
        })
    }