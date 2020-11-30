import asyncio
import websockets
import shlex

class Servidor:
    def __init__(self):
        self.onlines = []
    
    @property
    def nonlines(self):
        return len(self.onlines)
    
    async def conecta(self, websocket, path):
        cliente = Cliente(self, websocket, path)
        if cliente not in self.onlines:
            self.onlines.append(cliente)     
        await cliente.gerencia()

    def desconecta(self, cliente):
        if cliente in self.onlines:
            self.onlines.remove(cliente)        

    
    async def envia_a_todos(self, origem, mensagem):
        for cliente in self.onlines:            
            if origem != cliente and cliente.conectado:
                await cliente.envia("{0}: {1}".format(origem.nome, mensagem))

    
    async def envia_a_destinatario(self, origem, mensagem, destinatario):        
        for cliente in self.onlines:            
            if cliente.nome == destinatario and origem != cliente and cliente.conectado:
                await cliente.envia("Mensagem de {0}: {1}".format(origem.nome, mensagem))
                return True
        return False

    def verifica_nome(self, nome):
        for cliente in self.onlines:
            if cliente.nome and cliente.nome == nome:
                return False
        return True


class Cliente:    
    def __init__(self, servidor, websocket, path):
        self.cliente = websocket
        self.servidor = servidor
        self.nome = None        
    
    @property
    def conectado(self):
        return self.cliente.open

    
    async def gerencia(self):
        try:
            await self.envia("Bem vindo! Identifique-se com /nome SeuNome")
            while True:
                mensagem = await self.recebe()
                if mensagem:
                    await self.processa_comandos(mensagem)                                            
                else:
                    break
        except Exception:
            raise        
        finally:
            self.servidor.desconecta(self)

    
    async def envia(self, mensagem):
        await self.cliente.send(mensagem)

    
    async def recebe(self):
        mensagem = await self.cliente.recv()
        return mensagem

    
    async def processa_comandos(self, mensagem):        
        if mensagem.strip().startswith("/"):
            comandos=shlex.split(mensagem.strip()[1:])
            if len(comandos)==0:
                await self.envia("Comando vázio")
                return
            comando = comandos[0].lower()            
            if comando == "nome":
                await self.altera_nome(comandos)
            elif comando == "pvt":
                await self.pvt(comandos)
        else:
            if self.nome:
                await self.servidor.envia_a_todos(self, mensagem)
            else:
                await self.envia("Bem vindo! Identifique-se para enviar mensagens. Use o comando /nome SeuNome")

    
    async def altera_nome(self, comandos):                
        if len(comandos)>1 and self.servidor.verifica_nome(comandos[1]):
            self.nome = comandos[1]
            await self.envia("Nome alterado com sucesso para {0}".format(self.nome))
            await self.envia("Para enviar uma mensagem no privado utilize o comando /pvt Destinatário Mensagem".format(self.nome))
            await self.servidor.envia_a_todos(self, "entrou na sala.")

        else:
            await self.envia("Nome em uso ou inválido. Escolha um outro.")

    
    async def pvt(self, comandos):
        destinatario = comandos[1]
        mensagem = " ".join(comandos[2:])
        enviado = await self.servidor.envia_a_destinatario(self, mensagem, destinatario)
        if not enviado:
            await self.envia("Destinatário {0} não encontrado. Mensagem não enviada.".format(destinatario))

servidor=Servidor()
loop=asyncio.get_event_loop()

start_server = websockets.serve(servidor.conecta, "localhost", 50007)

try:
    loop.run_until_complete(start_server)
    loop.run_forever()
finally:
    start_server.close()
