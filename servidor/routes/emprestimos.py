from flask import Blueprint, request, jsonify, g
from models import Emprestimo
from auth import requer_autenticacao, requer_perfil
from . import erro_interno

emprestimos_bp = Blueprint("emprestimos", __name__)


@emprestimos_bp.route("/emprestimos", methods=["GET"])
@requer_autenticacao
def listar_emprestimos():
    usuario = g.usuario
    if usuario["perfil"] == "Usuário":
        emprestimos = Emprestimo.historico_usuario(usuario["usuario_id"])
    else:
        emprestimos = Emprestimo.listar()
    return jsonify(emprestimos), 200


@emprestimos_bp.route("/emprestimos", methods=["POST"])
@requer_perfil("Administrador", "Bibliotecário")
def criar_emprestimo():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    try:
        novo_id = Emprestimo.criar(dados)
        return jsonify({"mensagem": "Empréstimo registrado com sucesso!", "id": novo_id}), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify(erro_interno(e)), 500


@emprestimos_bp.route("/emprestimos/<int:id>", methods=["PUT"])
@requer_perfil("Administrador", "Bibliotecário")
def atualizar_emprestimo(id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    try:
        acao = dados.get("acao")
        if acao == "devolver":
            resultado = Emprestimo.devolver(id)
            mensagem = "Devolução registrada com sucesso!"
            if resultado.get("suspensao_aplicada"):
                mensagem += (f" Penalidade aplicada: {resultado['suspensao_aplicada']} dias de suspensão "
                             f"(dobro dos {resultado['dias_atraso']} dias de atraso).")
            return jsonify({"mensagem": mensagem, **resultado}), 200
        if acao == "renovar":
            resultado = Emprestimo.renovar(id)
            return jsonify({
                "mensagem": "Empréstimo renovado com sucesso!",
                **resultado
            }), 200
        return jsonify({"erro": "Ação inválida"}), 400
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify(erro_interno(e)), 500


@emprestimos_bp.route("/emprestimos/<int:id>/renovacoes", methods=["GET"])
@requer_autenticacao
def renovacoes_emprestimo(id):
    usuario = g.usuario
    if usuario["perfil"] == "Usuário":
        emprestimo = Emprestimo.buscar(id)
        if not emprestimo or emprestimo["usuario_id"] != usuario["usuario_id"]:
            return jsonify({"erro": "Empréstimo não encontrado."}), 404
    renovacoes = Emprestimo.renovacoes_do_emprestimo(id)
    return jsonify(renovacoes), 200


@emprestimos_bp.route("/emprestimos/contagem", methods=["GET"])
@requer_autenticacao
def contagem_emprestimos():
    emprestados = Emprestimo.contar_emprestados()
    atrasados = Emprestimo.contar_atrasados()
    devolvidos = Emprestimo.contar_devolvidos()
    return jsonify({
        "emprestados": emprestados,
        "atrasados": atrasados,
        "devolvidos": devolvidos
    }), 200


@emprestimos_bp.route("/emprestimos/ativos", methods=["GET"])
@requer_autenticacao
def listar_ativos():
    usuario = g.usuario
    if usuario["perfil"] == "Usuário":
        ativos = Emprestimo.listar_ativos_usuario(usuario["usuario_id"])
    else:
        ativos = Emprestimo.listar_ativos()
    return jsonify(ativos), 200


@emprestimos_bp.route("/emprestimos/historico", methods=["GET"])
@requer_autenticacao
def historico_emprestimos():
    usuario = g.usuario
    if usuario["perfil"] == "Usuário":
        historico = Emprestimo.historico_usuario(usuario["usuario_id"])
    else:
        historico = Emprestimo.historico()
    return jsonify(historico), 200
