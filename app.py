import os
import sqlite3
from flask import Flask, request, jsonify
from pagamento import cobrar

app = Flask(__name__)
DB = "loja.db"

def conectar():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def iniciar_banco():
    con = conectar()
    con.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY, nome TEXT, preco REAL)")
    con.execute("""CREATE TABLE IF NOT EXISTS usos_cupom (
        cliente_id TEXT, cupom TEXT, UNIQUE(cliente_id, cupom))""")
    if con.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
        con.executemany("INSERT INTO produtos (nome, preco) VALUES (?, ?)",
                        [("Caderno", 25.0), ("Caneta", 4.5), ("Mochila", 120.0)])
    con.commit()
    con.close()

@app.route("/produtos")
def listar():
    con = conectar()
    itens = [dict(l) for l in con.execute("SELECT * FROM produtos")]
    con.close()
    return jsonify(itens)

@app.route("/buscar")
def buscar():
    termo = request.args.get("q", "")
    con = conectar()
    sql = "SELECT * FROM produtos WHERE nome LIKE ?"
    itens = [dict(l) for l in con.execute(sql, (f"%{termo}%",))]
    con.close()
    return jsonify(itens)

@app.route("/finalizar", methods=["POST"])
def finalizar():
    dados = request.get_json(silent=True) or {}
    cliente = str(dados.get("cliente_id", "")).strip()
    itens = dados.get("itens", [])
    if not cliente or not isinstance(itens, list) or not itens:
        return jsonify({"erro": "Dados inválidos"}), 400

    con = conectar()
    total = 0.0
    for item in itens:
        try:
            pid, qtd = int(item["id"]), int(item["qtd"])
        except (KeyError, TypeError, ValueError):
            con.close()
            return jsonify({"erro": "Item inválido"}), 400
        if qtd < 1:
            con.close()
            return jsonify({"erro": "Quantidade inválida"}), 400
        linha = con.execute("SELECT preco FROM produtos WHERE id = ?", (pid,)).fetchone()
        if linha is None:
            con.close()
            return jsonify({"erro": "Produto inexistente"}), 400
        total += linha["preco"] * qtd

    if dados.get("cupom") == "PRIMEIRA10":
        ja_usou = con.execute(
            "SELECT 1 FROM usos_cupom WHERE cliente_id = ? AND cupom = ?",
            (cliente, "PRIMEIRA10")).fetchone()
        if ja_usou:
            con.close()
            return jsonify({"erro": "Cupom já utilizado"}), 400
        total *= 0.9
        con.execute("INSERT INTO usos_cupom (cliente_id, cupom) VALUES (?, ?)",
                    (cliente, "PRIMEIRA10"))
        con.commit()

    con.close()
    return jsonify(cobrar(round(total, 2)))

if __name__ == "__main__":
    iniciar_banco()
    app.run(host="127.0.0.1", port=5000, debug=os.getenv("FLASK_DEBUG") == "1")