"""As tabelas: contas, sessoes e locais salvos.

Tres e nada mais. O cache da API externa continua em memoria — cache que some
no restart e cache funcionando — e o conjunto de cidades do GeoNames continua
sendo o arquivo lido no boot, porque e dado que nunca muda. Ver a spec.

Este modulo descreve **o schema**, nao o acesso: quem le e escreve sao os
repositorios em `app/db/repositorio.py`, e e por eles que a aplicacao entra.
"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """A base declarativa. O Alembic compara o banco com `Base.metadata`."""


class Conta(Base):
    """A identidade que possui locais salvos, criada com e-mail e senha."""

    __tablename__ = "contas"

    id: Mapped[int] = mapped_column(primary_key=True)

    #: O e-mail e unico **sem diferenciar maiusculas**. A unicidade nao pode
    #: depender de o codigo lembrar de normalizar antes de inserir: o indice
    #: abaixo e sobre `lower(email)`, e o banco recusa a segunda conta mesmo
    #: que ela chegue por um caminho que esqueceu a normalizacao.
    email: Mapped[str] = mapped_column(String(320), nullable=False)

    #: O hash da senha, nunca a senha. O tamanho cobre com folga o formato do
    #: Argon2, que e o mais longo dos dois candidatos da spec.
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    #: `cascade="all, delete-orphan"` e o lado do ORM; `ondelete="CASCADE"` na
    #: chave estrangeira e o lado do banco. Os dois existem porque apagar uma
    #: conta por SQL direto tambem tem de levar os locais junto.
    locais_salvos: Mapped[list["LocalSalvo"]] = relationship(
        back_populates="conta", cascade="all, delete-orphan", passive_deletes=True
    )
    sessoes: Mapped[list["Sessao"]] = relationship(
        back_populates="conta", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        Index(
            "ix_contas_email_minusculo",
            text("lower(email)"),
            unique=True,
        ),
    )


class Sessao(Base):
    """A prova de que quem esta pedindo e o dono da conta.

    Uma conta pode ter varias sessoes ao mesmo tempo — e o mesmo dono em dois
    navegadores —, e por isso a conta **nao** e unica aqui. Ver ADR 0005.
    """

    __tablename__ = "sessoes"

    #: O identificador que viaja no cookie, e por isso e a propria chave: a
    #: busca por sessao acontece em toda requisicao autenticada, e uma chave
    #: substituta exigiria um indice a mais para a mesma consulta.
    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    conta_id: Mapped[int] = mapped_column(
        ForeignKey("contas.id", ondelete="CASCADE"), nullable=False, index=True
    )

    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    #: `timezone=True` nas duas colunas de instante: comparar expiracao com um
    #: `datetime` ingenuo levanta em Python e, pior, compara errado no SQL de
    #: quem roda em outro fuso.
    expira_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    conta: Mapped["Conta"] = relationship(back_populates="sessoes")


class LocalSalvo(Base):
    """Uma cidade que a pessoa guardou na sua conta.

    Guarda **os seis parametros que descrevem a cidade** — os mesmos que ja
    viajam na URL — e nada de clima: clima guardado envelhece, e alguem veria a
    temperatura de ontem sem saber que e de ontem.
    """

    __tablename__ = "locais_salvos"

    id: Mapped[int] = mapped_column(primary_key=True)

    conta_id: Mapped[int] = mapped_column(
        ForeignKey("contas.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    #: `country` pode vir vazio: a API externa **omite** o nome do pais para
    #: territorios e regioes especiais (Papeete, Hong Kong, Macau). Quem
    #: confirma a cidade e `country_code`, sempre presente.
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    admin1: Mapped[str | None] = mapped_column(String(200), nullable=True)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    #: A identidade do local **para efeito de nao duplicar**: a coordenada
    #: arredondada mais o codigo do pais. Comparar pelo nome falharia com
    #: grafias diferentes da mesma cidade, e comparar pela coordenada exata
    #: falharia com duas candidatas de precisao diferente.
    #:
    #: Coluna, e nao expressao no indice, porque o arredondamento e uma regra
    #: do dominio (as mesmas duas casas da chave do cache) e escreve-la em SQL
    #: a duplicaria num lugar onde ninguem a le.
    identidade: Mapped[str] = mapped_column(String(64), nullable=False)

    salvo_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    conta: Mapped["Conta"] = relationship(back_populates="locais_salvos")

    __table_args__ = (
        UniqueConstraint("conta_id", "identidade", name="uq_local_por_conta"),
    )
