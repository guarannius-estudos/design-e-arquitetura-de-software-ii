import logging
import azure.functions as func

app = func.FunctionApp()

from triggers.extract_categoria_produto import app as extract_categoria_produto
from triggers.extract_cliente import app as extract_cliente
from triggers.extract_entrega import app as extract_entrega
from triggers.extract_estoque_movimentacao import app as extract_estoque_movimentacao
from triggers.extract_estoque_saldo import app as extract_estoque_saldo
from triggers.extract_pedido_item import app as extract_pedido_item
from triggers.extract_pedido import app as extract_pedido
from triggers.extract_produto import app as extract_produto
from triggers.extract_regiao import app as extract_regiao
from triggers.extract_representante import app as extract_representante
from triggers.extract_titulo_receber import app as extract_titulo_receber
from triggers.extract_transportadora import app as extract_transportadora

app.register_functions(extract_categoria_produto)
app.register_functions(extract_cliente)
app.register_functions(extract_entrega)
app.register_functions(extract_estoque_movimentacao)
app.register_functions(extract_estoque_saldo)
app.register_functions(extract_pedido_item)
app.register_functions(extract_pedido)
app.register_functions(extract_produto)
app.register_functions(extract_regiao)
app.register_functions(extract_representante)
app.register_functions(extract_titulo_receber)
app.register_functions(extract_transportadora)