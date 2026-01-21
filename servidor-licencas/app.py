"""
Servidor de Licenciamento - RecalGuias
API Flask para gerenciar licenças remotamente
"""
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import hashlib
import secrets

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///licencas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ============ MODELOS DO BANCO ============

class Licenca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chave_licenca = db.Column(db.String(64), unique=True, nullable=False)
    cliente_nome = db.Column(db.String(200), nullable=False)
    cliente_email = db.Column(db.String(200))
    hardware_id = db.Column(db.String(200))
    ativa = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_expiracao = db.Column(db.DateTime)
    ultimo_acesso = db.Column(db.DateTime)
    total_acessos = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'chave_licenca': self.chave_licenca,
            'cliente_nome': self.cliente_nome,
            'cliente_email': self.cliente_email or 'N/A',
            'ativa': self.ativa,
            'data_criacao': self.data_criacao.strftime('%d/%m/%Y %H:%M'),
            'data_expiracao': self.data_expiracao.strftime('%d/%m/%Y') if self.data_expiracao else 'Vitalícia',
            'ultimo_acesso': self.ultimo_acesso.strftime('%d/%m/%Y %H:%M') if self.ultimo_acesso else 'Nunca',
            'total_acessos': self.total_acessos
        }

class LogAcesso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chave_licenca = db.Column(db.String(64), nullable=False)
    hardware_id = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50))
    sucesso = db.Column(db.Boolean)
    mensagem = db.Column(db.String(500))

# Criar tabelas
with app.app_context():
    db.create_all()

# ============ FUNÇÕES AUXILIARES ============

def gerar_chave_licenca():
    """Gera chave formato XXXX-XXXX-XXXX-XXXX"""
    raw = secrets.token_hex(8).upper()
    return f"{raw[0:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}"

def hash_hwid(hwid: str) -> str:
    """Hash SHA256 do hardware ID"""
    return hashlib.sha256(hwid.encode()).hexdigest()

# ============ ENDPOINTS ============

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'sistema': 'Servidor de Licenças - RecalGuias'
    })

@app.route('/api/health')
def health():
    return jsonify({'status': 'online'}), 200

@app.route('/api/validar', methods=['POST'])
def validar_licenca():
    """Endpoint principal - valida licença do cliente"""
    data = request.get_json()
    chave = data.get('chave_licenca')
    hwid = data.get('hardware_id')
    
    if not chave:
        return jsonify({'valida': False, 'mensagem': 'Chave não fornecida'}), 400
    
    licenca = Licenca.query.filter_by(chave_licenca=chave).first()
    
    log = LogAcesso(
        chave_licenca=chave,
        hardware_id=hwid,
        ip_address=request.remote_addr,
        sucesso=False,
        mensagem='Licença não encontrada'
    )
    
    if not licenca:
        db.session.add(log)
        db.session.commit()
        return jsonify({'valida': False, 'mensagem': 'Licença inválida'}), 404
    
    if not licenca.ativa:
        log.mensagem = 'Licença bloqueada'
        db.session.add(log)
        db.session.commit()
        return jsonify({'valida': False, 'mensagem': 'Licença bloqueada. Contate o suporte.'}), 403
    
    if licenca.data_expiracao and datetime.utcnow() > licenca.data_expiracao:
        log.mensagem = 'Licença expirada'
        db.session.add(log)
        db.session.commit()
        return jsonify({
            'valida': False,
            'mensagem': f'Licença expirou em {licenca.data_expiracao.strftime("%d/%m/%Y")}'
        }), 403
    
    # Hardware binding
    if hwid:
        hwid_hash = hash_hwid(hwid)
        if not licenca.hardware_id:
            licenca.hardware_id = hwid_hash
        elif licenca.hardware_id != hwid_hash:
            log.mensagem = 'Hardware diferente'
            db.session.add(log)
            db.session.commit()
            return jsonify({'valida': False, 'mensagem': 'Licença vinculada a outro computador'}), 403
    
    # ✅ VÁLIDA
    licenca.ultimo_acesso = datetime.utcnow()
    licenca.total_acessos += 1
    
    log.sucesso = True
    log.mensagem = 'Acesso permitido'
    
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'valida': True,
        'mensagem': 'Licença válida',
        'cliente_nome': licenca.cliente_nome,
        'expira_em': licenca.data_expiracao.isoformat() if licenca.data_expiracao else None
    }), 200

@app.route('/api/admin/criar_licenca', methods=['POST'])
def criar_licenca():
    """Criar nova licença"""
    data = request.get_json()
    cliente_nome = data.get('cliente_nome')
    cliente_email = data.get('cliente_email')
    dias_validade = data.get('dias_validade')
    
    if not cliente_nome:
        return jsonify({'erro': 'Nome obrigatório'}), 400
    
    chave = gerar_chave_licenca()
    
    data_exp = None
    if dias_validade:
        data_exp = datetime.utcnow() + timedelta(days=dias_validade)
    
    nova_licenca = Licenca(
        chave_licenca=chave,
        cliente_nome=cliente_nome,
        cliente_email=cliente_email,
        data_expiracao=data_exp,
        ativa=True
    )
    
    db.session.add(nova_licenca)
    db.session.commit()
    
    return jsonify({
        'sucesso': True,
        'chave_licenca': chave,
        'cliente_nome': cliente_nome,
        'expira_em': data_exp.strftime('%d/%m/%Y') if data_exp else 'Vitalícia'
    }), 201

@app.route('/api/admin/bloquear/<chave>', methods=['POST'])
def bloquear_licenca(chave):
    """Bloquear licença"""
    licenca = Licenca.query.filter_by(chave_licenca=chave).first()
    if not licenca:
        return jsonify({'erro': 'Licença não encontrada'}), 404
    
    licenca.ativa = False
    db.session.commit()
    
    return jsonify({'sucesso': True, 'mensagem': f'Licença {chave} bloqueada'})

@app.route('/api/admin/ativar/<chave>', methods=['POST'])
def ativar_licenca(chave):
    """Ativar licença"""
    licenca = Licenca.query.filter_by(chave_licenca=chave).first()
    if not licenca:
        return jsonify({'erro': 'Licença não encontrada'}), 404
    
    licenca.ativa = True
    db.session.commit()
    
    return jsonify({'sucesso': True, 'mensagem': f'Licença {chave} ativada'})

@app.route('/api/admin/listar', methods=['GET'])
def listar_licencas():
    """Listar todas"""
    licencas = Licenca.query.order_by(Licenca.data_criacao.desc()).all()
    return jsonify({
        'total': len(licencas),
        'licencas': [l.to_dict() for l in licencas]
    })

@app.route('/api/admin/logs/<chave>', methods=['GET'])
def ver_logs(chave):
    """Ver logs de uma licença"""
    logs = LogAcesso.query.filter_by(chave_licenca=chave).order_by(
        LogAcesso.timestamp.desc()
    ).limit(50).all()
    
    return jsonify({
        'total': len(logs),
        'logs': [{
            'timestamp': log.timestamp.strftime('%d/%m/%Y %H:%M:%S'),
            'ip': log.ip_address,
            'sucesso': log.sucesso,
            'mensagem': log.mensagem
        } for log in logs]
    })

@app.route('/admin')
def painel_admin():
    """Painel administrativo"""
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
