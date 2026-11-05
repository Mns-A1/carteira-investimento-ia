"""Cria dados de demonstração: python -m src.seed"""
from datetime import date

from .app import config, models, security
from .app.database import Base, SessionLocal, engine


def main():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    if db.query(models.Usuario).filter_by(email="investidor@demo.com").first():
        print("Os dados de demonstração já existem.")
        return

    def usuario(nome, email, perfil):
        u = models.Usuario(nome=nome, email=email, senha_hash=security.hash_senha("demo1234"), perfil=perfil)
        db.add(u)
        db.flush()
        return u

    consultor = models.Consultor(usuario_id=usuario("Carla Consultora", "consultor@demo.com", "consultor").id)
    db.add(consultor)
    db.flush()
    investidor = models.Investidor(usuario_id=usuario("Pedro Investidor", "investidor@demo.com", "investidor").id,
                                   perfil_risco="moderado", limite_concentracao=config.LIMITE_CONCENTRACAO_PADRAO,
                                   consultor_id=consultor.id)
    db.add(investidor)
    db.flush()
    carteira = models.Carteira(investidor_id=investidor.id)
    db.add(carteira)
    db.flush()
    for tipo, nome, valor in [("acao", "ITUB3", 4000), ("acao", "PRIO3", 2000),
                              ("tesouro_selic", "Tesouro Selic 2029", 2500), ("cdb", "CDB Banco Inter", 1500)]:
        db.add(models.Investimento(carteira_id=carteira.id, tipo=tipo, nome=nome, valor_aplicado=valor,
                                   data_aplicacao=date.today()))
    db.commit()
    print("Demonstração criada (senha de ambos: demo1234):\n  investidor@demo.com\n  consultor@demo.com")


if __name__ == "__main__":
    main()
