"""planos

A tabela dos planos: o que alguem pretende fazer num dia, guardado na sua
conta. A quarta e ultima tabela da entrega do Calendario.

Gerada por `--autogenerate` a partir de `app/db/schema.py`, onde cada coluna
esta comentada, e conferida a mao. Tres pontos que o SQL abaixo mostra e valem
conhecer:

- `dia` e `DATE`, e **nao** `TIMESTAMP`. A ausencia de hora e decisao de
  dominio — a aptidao e diaria e o horizonte longo nao tem dado horario —, e o
  tipo e o que impede que uma hora entre por descuido (verbete *Plano*).
- `ck_planos_atividade` fecha `atividade` nas quatro que a regra do backend
  julga. Texto livre permitiria um plano cuja atividade **nenhuma regra julga**,
  e a faixa nao teria aptidao para cruzar com ele. `CHECK` e nao `ENUM` nativo:
  acrescentar a quinta atividade e alterar uma restricao, e nao um `ALTER TYPE`
  que no Postgres nao roda em toda transacao.
- a chave estrangeira e `ON DELETE CASCADE`, como as outras duas: apagar uma
  conta leva seus planos junto, inclusive por SQL direto.

**Nenhuma coluna de clima**, pela mesma regra de `locais_salvos`: clima
guardado envelhece, e alguem veria a previsao de anteontem sem saber que e de
anteontem. O plano guarda intencao; a previsao e buscada fresca na leitura.

Revision ID: 3e97e4c5740c
Revises: f9caeb6221c0
Create Date: 2026-09-17 18:29:51.237609

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e97e4c5740c'
down_revision: Union[str, Sequence[str], None] = 'f9caeb6221c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('planos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('conta_id', sa.Integer(), nullable=False),
    sa.Column('titulo', sa.String(length=200), nullable=False),
    sa.Column('dia', sa.Date(), nullable=False),
    sa.Column('atividade', sa.String(length=20), nullable=False),
    sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("atividade IN ('lavar_roupa', 'esporte', 'viagem', 'plantio')", name='ck_planos_atividade'),
    sa.ForeignKeyConstraint(['conta_id'], ['contas.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_planos_conta_id'), 'planos', ['conta_id'], unique=False)
    # `dia` indexado porque a listagem ordena por ele, e e a consulta que a
    # faixa de planos faz a cada carregamento da pagina.
    op.create_index(op.f('ix_planos_dia'), 'planos', ['dia'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_planos_dia'), table_name='planos')
    op.drop_index(op.f('ix_planos_conta_id'), table_name='planos')
    op.drop_table('planos')
