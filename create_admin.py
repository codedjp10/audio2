"""
Script de inicialização do sistema.

O que ele faz:
1. Cria todas as tabelas do banco de dados (se ainda não existirem).
2. Popula categorias, locais e status padrão (só na primeira vez).
3. Cria o primeiro usuário ADMINISTRADOR, perguntando nome/e-mail/senha.

Uso:
    python create_admin.py
"""

import getpass
import re

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.category import Category
from app.models.location import Location

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def seed_defaults(app):
    created_categories = 0
    for name, kind in app.config["DEFAULT_CATEGORIES"]:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name, kind=kind))
            created_categories += 1

    created_locations = 0
    for name in app.config["DEFAULT_LOCATIONS"]:
        if not Location.query.filter_by(name=name).first():
            db.session.add(Location(name=name))
            created_locations += 1

    db.session.commit()
    print(f"✓ {created_categories} categoria(s) padrão criada(s).")
    print(f"✓ {created_locations} local(is) padrão criado(s).")


def prompt_admin():
    print("\n--- Criar usuário administrador ---")
    name = input("Nome completo: ").strip()
    while not name:
        name = input("Nome completo (obrigatório): ").strip()

    email = input("E-mail: ").strip().lower()
    while not EMAIL_RE.match(email):
        email = input("E-mail inválido. Digite novamente: ").strip().lower()

    if User.query.filter_by(email=email).first():
        print("Já existe um usuário com esse e-mail. Nenhum usuário foi criado.")
        return

    password = getpass.getpass("Senha (mínimo 6 caracteres): ")
    while len(password) < 6:
        password = getpass.getpass("Senha muito curta. Digite novamente: ")

    confirm = getpass.getpass("Confirme a senha: ")
    while confirm != password:
        confirm = getpass.getpass("As senhas não coincidem. Confirme novamente: ")

    admin = User(name=name, email=email, role="admin", active=True)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f"\n✓ Administrador '{name}' <{email}> criado com sucesso!")


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✓ Tabelas do banco de dados criadas/verificadas.")
        seed_defaults(app)

        if User.query.filter_by(role="admin").first():
            print("\nJá existe pelo menos um administrador cadastrado.")
            resp = input("Deseja criar outro administrador mesmo assim? (s/N): ").strip().lower()
            if resp != "s":
                print("Nenhuma alteração feita. Pronto!")
                return

        prompt_admin()


if __name__ == "__main__":
    main()
