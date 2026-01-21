class FebrabanValidator:
    @staticmethod
    def validar(linha_digitavel: str) -> dict:
        """
        Valida linha digitável (Boleto Bancário ou Arrecadação).
        Retorna: {'valido': bool, 'tipo': str, 'mensagem': str}
        """
        # Remove caracteres não numéricos
        codigo = ''.join(filter(str.isdigit, linha_digitavel))
        
        if len(codigo) not in (47, 48):
             return {
                 'valido': False, 
                 'tipo': 'Desconhecido', 
                 'mensagem': f'Tamanho inválido: {len(codigo)} dígitos. Esperado 47 (Cobrança) ou 48 (Arrecadação).'
             }
        
        tipo = 'Cobrança' if len(codigo) == 47 else 'Arrecadação'
        
        # Validar dígito verificador geral (básico)
        # Implementação completa exigiria separar os campos e calcular Mod10/11
        # Para MVP FASE 1, validamos formato básico
        
        if tipo == 'Arrecadação':
            if not codigo.startswith('8'):
                return {'valido': False, 'tipo': tipo, 'mensagem': 'Guia de arrecadação deve começar com 8.'}
                
            # Identificação do órgão pelo segmento (dígito 2)
            # 1. Prefeituras; 2. Saneamento; 3. Energia; 4. Gas; 5. Telecom; 6. Órgãos Governamentais; 7. Multas; 9. Outros
            segmento = codigo[1]
            orgao_map = {
                '1': 'Prefeitura', '2': 'Saneamento', '3': 'Energia', '4': 'Gás',
                '5': 'Telecom', '6': 'Órgãos Gov', '7': 'Multas', '9': 'Outros'
            }
            orgao = orgao_map.get(segmento, 'Desconhecido')
            return {'valido': True, 'tipo': tipo, 'orgao': orgao, 'mensagem': 'Formato válido'}
            
        return {'valido': True, 'tipo': tipo, 'mensagem': 'Formato válido'}
