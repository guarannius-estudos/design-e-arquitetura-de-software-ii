import logging
import azure.functions as func

app = func.FunctionApp()

from triggers.extract_categoria_produto import app as extract_categoria_produto
from triggers.extract_cliente import app as extract_cliente
from triggers.extract_pedido import app as extract_pedido

app.register_functions(extract_categoria_produto)
app.register_functions(extract_cliente)
app.register_functions(extract_pedido)