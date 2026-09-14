"""Catalogo rico da seed de marketplace. Nao entra em seed_all."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.catalog.models import Offer, Product, Seller
from app.catalog.seed import SELLER_A_ID, SELLER_B_ID, add_if_missing

SELLER_TECH_ID = UUID("55555555-5555-5555-5555-555555555551")
SELLER_CASA_ID = UUID("55555555-5555-5555-5555-555555555552")
SELLER_ESPORTE_ID = UUID("55555555-5555-5555-5555-555555555553")
SELLER_LIVROS_ID = UUID("55555555-5555-5555-5555-555555555554")
SELLER_MODA_ID = UUID("55555555-5555-5555-5555-555555555555")
SELLER_KIDS_ID = UUID("55555555-5555-5555-5555-555555555556")

DEMO_SELLERS = (
    Seller(id=SELLER_TECH_ID, name="Tech Hub"),
    Seller(id=SELLER_CASA_ID, name="Casa Viva"),
    Seller(id=SELLER_ESPORTE_ID, name="Esporte Total"),
    Seller(id=SELLER_LIVROS_ID, name="Livraria Norte"),
    Seller(id=SELLER_MODA_ID, name="Moda Urban"),
    Seller(id=SELLER_KIDS_ID, name="Kids World"),
)

PRODUCTS: tuple[tuple[int, str, str], ...] = (
    (1, "Notebook 14 polegadas", "Ultrabook para trabalho e estudo, 16 GB RAM."),
    (2, "Monitor 27 polegadas", "Painel IPS Full HD com suporte ajustavel."),
    (3, "Fone Bluetooth", "Fone intra-auricular com estojo carregador."),
    (4, "SSD 1 TB", "Unidade NVMe para upgrade de notebook."),
    (5, "Teclado mecanico", "Switch linear, layout ABNT2 e RGB."),
    (6, "Webcam Full HD", "Camera com microfone para chamadas."),
    (7, "Carregador USB-C", "Fonte 30 W compativel com notebooks leves."),
    (8, "Smartphone flagship", "Aparelho top de linha com 256 GB."),
    (9, "Camiseta basica", "Algodao 100%, corte reto, varias cores."),
    (10, "Calca jeans", "Jeans reta com elastano, lavagem media."),
    (11, "Jaqueta corta-vento", "Corta-vento leve com capuz."),
    (12, "Tenis casual", "Solado borracha e cabedal em lona."),
    (13, "Vestido midi", "Tecido fluido, manga curta."),
    (14, "Cinto de couro", "Fivela metalica, largura 3 cm."),
    (15, "Relogio analogico", "Caixa 40 mm, pulseira de couro."),
    (16, "Jogo de panelas", "5 pecas antiaderentes com tampas."),
    (17, "Aspirador vertical", "Sem fio, autonomia de 40 minutos."),
    (18, "Luminaria de mesa", "Braco articulado e luz branca ajustavel."),
    (19, "Jogo de cama queen", "200 fios, inclui fronhas."),
    (20, "Cafeteira eletrica", "Jarra de 15 xicaras com placa aquecida."),
    (21, "Bola de futebol", "Campo oficial, costura termica."),
    (22, "Tapete de yoga", "6 mm, antiderrapante."),
    (23, "Garrafa termica", "750 ml, inox, mantem 12 h."),
    (24, "Bicicleta urbana", "Aro 29, 21 marchas."),
    (25, "Livro de receitas", "200 receitas brasileiras ilustradas."),
    (26, "Romance contemporaneo", "Edicao de bolso, 320 paginas."),
    (27, "Guia pratico de Python", "Introducao objetiva para iniciantes."),
    (28, "Historia do Brasil", "Panorama ilustrado do seculo XVI ao XX."),
    (29, "Blocos de montar 500 pecas", "Kit criativo a partir de 6 anos."),
    (30, "Boneca articulada", "30 cm, roupas trocaveis."),
    (31, "Quebra-cabeca 1000 pecas", "Paisagem litoranea."),
    (32, "Carrinho de controle remoto", "Alcance 30 m, bateria recarregavel."),
)

# n, product_n, seller_id, price, base_stock, available
OFFERS: tuple[tuple[int, int, UUID, str, int, bool], ...] = (
    (1, 1, SELLER_A_ID, "3499.00", 20, True),
    (2, 1, SELLER_TECH_ID, "3299.00", 16, True),
    (3, 2, SELLER_A_ID, "1299.00", 12, True),
    (4, 3, SELLER_A_ID, "199.00", 50, True),
    (5, 3, SELLER_TECH_ID, "179.00", 30, True),
    (6, 4, SELLER_TECH_ID, "499.00", 24, True),
    (7, 5, SELLER_A_ID, "349.00", 18, True),
    (8, 5, SELLER_TECH_ID, "329.00", 20, True),
    (9, 6, SELLER_TECH_ID, "259.00", 32, True),
    (10, 7, SELLER_A_ID, "39.90", 90, True),
    (11, 8, SELLER_A_ID, "5499.00", 6, True),
    (12, 8, SELLER_TECH_ID, "5299.00", 1, True),
    (13, 9, SELLER_B_ID, "49.90", 110, True),
    (14, 9, SELLER_MODA_ID, "39.90", 70, True),
    (15, 10, SELLER_B_ID, "189.00", 30, True),
    (16, 11, SELLER_B_ID, "299.00", 16, True),
    (17, 12, SELLER_B_ID, "249.00", 22, True),
    (18, 12, SELLER_A_ID, "259.00", 12, True),
    (19, 13, SELLER_MODA_ID, "219.00", 10, True),
    (20, 14, SELLER_B_ID, "79.00", 5, False),
    (21, 15, SELLER_B_ID, "899.00", 8, True),
    (22, 16, SELLER_CASA_ID, "349.00", 18, True),
    (23, 17, SELLER_CASA_ID, "799.00", 9, True),
    (24, 18, SELLER_CASA_ID, "119.00", 24, True),
    (25, 19, SELLER_CASA_ID, "159.00", 20, True),
    (26, 20, SELLER_CASA_ID, "429.00", 3, False),
    (27, 21, SELLER_ESPORTE_ID, "89.00", 44, True),
    (28, 22, SELLER_ESPORTE_ID, "79.90", 38, True),
    (29, 23, SELLER_ESPORTE_ID, "59.90", 52, True),
    (30, 24, SELLER_ESPORTE_ID, "2499.00", 6, True),
    (31, 25, SELLER_LIVROS_ID, "59.90", 42, True),
    (32, 26, SELLER_LIVROS_ID, "44.90", 32, True),
    (33, 27, SELLER_LIVROS_ID, "119.00", 22, True),
    (34, 28, SELLER_LIVROS_ID, "69.90", 10, False),
    (35, 29, SELLER_KIDS_ID, "189.00", 16, True),
    (36, 30, SELLER_KIDS_ID, "129.00", 18, True),
    (37, 31, SELLER_KIDS_ID, "79.90", 22, True),
    (38, 32, SELLER_KIDS_ID, "159.00", 12, True),
    (39, 2, SELLER_TECH_ID, "1199.00", 8, True),
    (40, 10, SELLER_MODA_ID, "199.00", 13, True),
    (41, 16, SELLER_A_ID, "379.00", 10, True),
    (42, 21, SELLER_A_ID, "99.00", 20, True),
    (43, 25, SELLER_A_ID, "64.90", 24, True),
    (44, 7, SELLER_TECH_ID, "34.90", 2, True),
    (45, 11, SELLER_MODA_ID, "279.00", 11, True),
    (46, 4, SELLER_A_ID, "519.00", 9, True),
)

OFFER_BY_N = {row[0]: row for row in OFFERS}


def product_id(n: int) -> UUID:
    return UUID(f"01000001-0000-4000-8000-{n:012x}")


def offer_id(n: int) -> UUID:
    return UUID(f"01000002-0000-4000-8000-{n:012x}")


def offer_price(n: int) -> Decimal:
    return Decimal(OFFER_BY_N[n][3])


def offer_base_stock(n: int) -> int:
    return OFFER_BY_N[n][4]


def seed_demo_sellers(session: Session) -> None:
    """Insere os seis vendedores extras da demonstracao."""
    for seller in DEMO_SELLERS:
        add_if_missing(session, Seller(id=seller.id, name=seller.name))


def seed_demo_catalog(session: Session) -> None:
    """Insere produtos e ofertas com estoque-base (antes do consumo)."""
    for n, name, description in PRODUCTS:
        add_if_missing(session, Product(id=product_id(n), name=name, description=description))
    session.flush()
    for n, product_n, seller_id, price, base_stock, available in OFFERS:
        add_if_missing(
            session,
            Offer(
                id=offer_id(n),
                product_id=product_id(product_n),
                seller_id=seller_id,
                price=Decimal(price),
                stock=base_stock,
                available=available,
            ),
        )
