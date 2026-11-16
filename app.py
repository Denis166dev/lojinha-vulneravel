import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
DB = "loja.db"

def conectar():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def iniciar_banco():
    con = conectar()
    con.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY, nome TEXT, preco REAL)")
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

if __name__ == "__main__":
    iniciar_banco()
    app.run(host="127.0.0.1", port=5000)