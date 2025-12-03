"""
Normalização de texto para transcrições de áudio

Converte números, símbolos e caracteres especiais para forma falada em português.
"""
import re
from num2words import num2words
from typing import Dict


class TextNormalizer:
    """Normaliza texto convertendo números e símbolos para forma falada."""
    
    # Mapeamento de símbolos comuns
    SYMBOL_MAP = {
        '%': ' porcento',
        '&': ' e ',
        '@': ' arroba ',
        '#': ' hashtag ',
        '$': ' dólares ',
        'R$': ' reais ',
        '€': ' euros ',
        '£': ' libras ',
        '+': ' mais ',
        '-': ' menos ',
        '×': ' vezes ',
        '÷': ' dividido por ',
        '=': ' igual ',
        '<': ' menor que ',
        '>': ' maior que ',
        '/': ' barra ',
        '\\': ' contrabarra ',
    }
    
    def __init__(self, lang='pt_BR'):
        """
        Inicializa o normalizador.
        
        Args:
            lang: Código do idioma (pt_BR para português brasileiro)
        """
        self.lang = lang
    
    def normalize_percentage(self, text: str) -> str:
        """
        Converte percentuais para forma falada.
        
        Exemplos:
            '3%' -> 'três porcento'
            '10.5%' -> 'dez vírgula cinco porcento'
            '100%' -> 'cem porcento'
        """
        # Padrão: número seguido de %
        pattern = r'(\d+(?:[.,]\d+)?)%'
        
        def replace_percentage(match):
            num_str = match.group(1).replace(',', '.')
            num = float(num_str)
            num_words = num2words(num, lang=self.lang)
            return f'{num_words} porcento'
        
        return re.sub(pattern, replace_percentage, text)
    
    def normalize_currency(self, text: str) -> str:
        """
        Converte valores monetários para forma falada.
        
        Exemplos:
            'R$ 100' -> 'cem reais'
            '$50' -> 'cinquenta dólares'
            'R$1.500,00' -> 'mil e quinhentos reais'
        """
        # R$ ou reais
        pattern_brl = r'R\$\s*(\d+(?:[.,]\d+)*)'
        
        def replace_brl(match):
            num_str = match.group(1).replace('.', '').replace(',', '.')
            num = float(num_str)
            num_words = num2words(num, lang=self.lang)
            return f'{num_words} reais'
        
        text = re.sub(pattern_brl, replace_brl, text)
        
        # Dólar
        pattern_usd = r'\$\s*(\d+(?:[.,]\d+)*)'
        
        def replace_usd(match):
            num_str = match.group(1).replace(',', '.')
            num = float(num_str)
            num_words = num2words(num, lang=self.lang)
            return f'{num_words} dólares'
        
        text = re.sub(pattern_usd, replace_usd, text)
        
        return text
    
    def normalize_numbers(self, text: str) -> str:
        """
        Converte números para forma falada.
        
        Exemplos:
            '2025' -> 'dois mil e vinte e cinco'
            '3.5' -> 'três vírgula cinco'
            '1,000' -> 'mil'
        """
        # Números com vírgula/ponto decimal
        pattern_decimal = r'\b(\d+)[.,](\d+)\b'
        
        def replace_decimal(match):
            integer_part = int(match.group(1))
            decimal_part = match.group(2)
            
            integer_words = num2words(integer_part, lang=self.lang)
            decimal_words = ' '.join([num2words(int(d), lang=self.lang) for d in decimal_part])
            
            return f'{integer_words} vírgula {decimal_words}'
        
        text = re.sub(pattern_decimal, replace_decimal, text)
        
        # Números inteiros
        pattern_integer = r'\b(\d+)\b'
        
        def replace_integer(match):
            num = int(match.group(1))
            return num2words(num, lang=self.lang)
        
        text = re.sub(pattern_integer, replace_integer, text)
        
        return text
    
    def normalize_symbols(self, text: str) -> str:
        """
        Converte símbolos para forma falada.
        
        Exemplos:
            'A & B' -> 'A e B'
            'email@domain.com' -> 'email arroba domain ponto com'
        """
        for symbol, replacement in self.SYMBOL_MAP.items():
            text = text.replace(symbol, replacement)
        
        return text
    
    def normalize_ordinals(self, text: str) -> str:
        """
        Converte ordinais para forma falada.
        
        Exemplos:
            '1º' -> 'primeiro'
            '2ª' -> 'segunda'
        """
        pattern = r'(\d+)[ºª°]'
        
        def replace_ordinal(match):
            num = int(match.group(1))
            return num2words(num, lang=self.lang, ordinal=True)
        
        return re.sub(pattern, replace_ordinal, text)
    
    def clean_whitespace(self, text: str) -> str:
        """Remove espaços múltiplos e ajusta pontuação."""
        # Múltiplos espaços -> um espaço
        text = re.sub(r'\s+', ' ', text)
        
        # Espaço antes de pontuação
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        # Espaço depois de pontuação
        text = re.sub(r'([.,!?;:])([^\s])', r'\1 \2', text)
        
        return text.strip()
    
    def normalize(self, text: str) -> str:
        """
        Normalização completa do texto.
        
        Aplica todas as normalizações na ordem correta:
        1. Moeda
        2. Percentuais
        3. Ordinais
        4. Números
        5. Símbolos
        6. Limpeza de espaços
        
        Args:
            text: Texto original
            
        Returns:
            Texto normalizado
        """
        # Ordem importa! Moeda e % antes de números genéricos
        text = self.normalize_currency(text)
        text = self.normalize_percentage(text)
        text = self.normalize_ordinals(text)
        text = self.normalize_numbers(text)
        text = self.normalize_symbols(text)
        text = self.clean_whitespace(text)
        
        return text.lower()


def normalize_text(text: str, lang: str = 'pt_BR') -> str:
    """
    Função auxiliar para normalização rápida.
    
    Args:
        text: Texto a normalizar
        lang: Idioma (padrão: pt_BR)
        
    Returns:
        Texto normalizado
    """
    normalizer = TextNormalizer(lang=lang)
    return normalizer.normalize(text)


if __name__ == "__main__":
    # Testes
    normalizer = TextNormalizer()
    
    test_cases = [
        "Em 2025 tivemos 3% de crescimento",
        "O produto custa R$ 1.500,00",
        "Valor de $100 dólares",
        "Chegou em 1º lugar com 95.5% dos votos",
        "A taxa é de 10,5% ao ano",
        "Vendemos 1000 unidades",
        "Email: contato@empresa.com.br",
        "A & B Company",
        "Resultado: 50/50",
    ]
    
    print("=" * 80)
    print("TESTES DE NORMALIZAÇÃO DE TEXTO")
    print("=" * 80)
    
    for test in test_cases:
        normalized = normalizer.normalize(test)
        print(f"\nOriginal:    {test}")
        print(f"Normalizado: {normalized}")
