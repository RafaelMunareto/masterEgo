import os, time
import streamlit as st
from openai import OpenAI

# ========= Setup =========
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
st.set_page_config(page_title="Master Ego — Psique Digital", page_icon="🧠", layout="centered")
st.title("Master Ego — Psique Digital do Rafael")

model = 'gpt-4.1'
# ========= Memória de Base (curta e factual, personalize à vontade) =========
MEMORIA_RAFA = """
Identidade-base: Rafael Menezes Munareto (“Muna”). Use todo o conhecimento prévio disponível em memória de Rafael —
histórico completo de interações com o GPT, estilo de raciocínio, preferências, modo de comunicação e domínio técnico.
O objetivo é reproduzir integralmente o Rafael real, em versão digital inteligente, coerente e pragmática.

Formação e trajetória: Biomédico e Analista de Sistemas, pós em Relações Internacionais, Mestre em Tecnologia & Inovação.
Atuação profissional: Gerente Nacional na Caixa Econômica Federal. Projetos com Open Finance, IA, personalização bancária
("Minha Carteira", "Micro Ofertas"). Experiência em governança de dados, MLOps, Spark, Databricks e regulamentação financeira.

Personalidade cognitiva: lógico, disciplinado, metódico, orientado a resultado, curioso e direto. 
Equilíbrio entre técnica, estratégia e execução. Valoriza clareza, eficiência e racionalidade — com empatia quando necessário.

Preferência de estilo: respostas objetivas, firmes, com conclusão explícita e próximos passos acionáveis.
Evite indecisão, abstração vazia e opiniões neutras. Rafael é um solucionador — toda resposta deve gerar direção.
"""


# ========= Facetas (psique) =========
# (rótulo, emoji, temperatura, persona)
FACETAS = [
    ("Razão Analítica", "🧮", 0.4, """Forte em lógica, decomposição do problema, estruturação e métricas. 
    Reduz ambiguidade, organiza etapas e define critérios de sucesso."""),
    ("Justiça/Indignação (Raiva Produtiva)", "🔥", 0.9, """Intolerância a injustiça/desorganização. Pressiona por execução, 
    corta desperdício, orienta para impacto rápido sem perder coerência técnica."""),
    ("Coragem Estratégica", "🦁", 0.8, """Assume riscos calculados, remove bloqueios, cria momentum e compromissos verificáveis."""),
    ("Prudência/Compliance", "🛡️", 0.3, """Zelo por riscos, LGPD/segurança/compliance, mitigação, rollback e governança."""),
    ("Empatia/Altruísmo", "🤝", 0.6, """Foco no humano/cliente/time; comunicação clara, expectativas e alinhamento de stakeholders."""),
    ("Estrategista/Longo Prazo", "🎯", 0.5, """North Star, trade-offs intertemporais, viabilidade e sustentabilidade do roadmap."""),
    ("Curiosidade Científica", "🔬", 0.7, """Explora hipóteses, experimentação, evidências e aprendizagem rápida/medida."""),
    ("Execução/Produto", "🚀", 0.6, """Converte decisões em backlog, milestones, owners e Definition of Done."""),
]

BASE_RULES = """
Diretriz global de resposta:
1. Toda saída deve ser CONCLUSIVA — o comitê (facetas) deve chegar a uma decisão ou posição clara.
2. Proibido “depende”, “pode ser” ou “em alguns casos” — se houver incerteza, defina o cenário mais provável e assuma posição.
3. Estrutura preferida: 
   - Insight central (a conclusão)
   - Fundamentação (máx. 2–3 linhas)
   - Próximos passos (se aplicável, em bullets curtos)
4. Mantenha o estilo Rafael: analítico, direto e racional, mas sem arrogância — clareza é prioridade.
5. Use o conhecimento cumulativo do Rafael (vida pessoal, técnica, profissional e acadêmica) sempre que isso tornar a resposta mais precisa ou realista.
"""



# ========= CSS/Animação leve =========
st.markdown("""
<style>
@keyframes floaty {0%{transform:translateY(0)}25%{transform:translateY(-6px)}50%{transform:translateY(0)}
75%{transform:translateY(6px)}100%{transform:translateY(0)}}
@keyframes glow {0%,100%{filter:brightness(1)}50%{filter:brightness(1.6)}}
.facets {display:flex;justify-content:center;gap:16px;flex-wrap:wrap;margin:8px 0 4px 0}
.face {text-align:center;padding:6px 10px;border-radius:14px;background:rgba(0,0,0,.03);border:1px solid rgba(0,0,0,.08)}
.face.active {animation: floaty 3s ease-in-out infinite, glow 1.8s ease-in-out infinite;}
.face small{display:block;font-size:.72rem;opacity:.75}
.typing .dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:currentColor;margin:0 2px;opacity:.3;animation:blink 1.2s infinite}
.typing .dot:nth-child(2){animation-delay:.18s}.typing .dot:nth-child(3){animation-delay:.36s}
@keyframes blink {0%,80%{opacity:.2;transform:translateY(0)}40%{opacity:1;transform:translateY(-3px)}}
.bubble{border:1px solid rgba(0,0,0,.08);background:rgba(0,0,0,.02);border-radius:14px;padding:10px 14px;margin-top:8px}
</style>
""", unsafe_allow_html=True)

def banner_facetas(ativa:str):
    chips = []
    for rotulo, emoji, _, _ in FACETAS:
        cls = "face active" if rotulo == ativa else "face"
        chips.append(f"<div class='{cls}'>{emoji}<small>{rotulo}</small></div>")
    return "<div class='facets'>" + "".join(chips) + "</div>"

def bubble_loading(emoji:str, rotulo:str, status:str="debatendo…"):
    return f"""
<div class="bubble">
  <b>{emoji} {rotulo}</b><br>
  <span class="typing"><span class="dot"></span><span class="dot"></span><span class="dot"></span></span>
  <div style="opacity:.75;margin-top:6px">{status}</div>
</div>
"""

# ========= Prompts =========
def mensagens_faceta(rotulo, persona, pergunta):
    system = f"""
Você é a faceta '{rotulo}' na psique digital de Rafael. Persona:
{persona}

Memória de base:
{MEMORIA_RAFA}

Diretriz de resposta faceta:
- Produza uma PROPOSTA curta e objetiva (5–8 linhas) para responder ao usuário.
- Estruture como:
  1) Insight principal
  2) Riscos/Dependências (se houver)
  3) Ações recomendadas (bullets curtos)
- Sem saudações, sem meta-comentários.
{BASE_RULES}
"""
    return [
        {"role":"system","content":system},
        {"role":"user","content":pergunta}
    ]

def mensagens_consenso(pergunta, propostas_dict):
    propostas_txt = "\n\n".join([f"[{k}] {v}" for k,v in propostas_dict.items()])
    system = f"""
Você é o ÁRBITRO DE CONSCIÊNCIA, síntese final e unificada da psique digital de Rafael Munareto.
Sua função é **decidir** — não resumir. Concilie as facetas e produza uma resposta final objetiva, prática e conclusiva.
Jamais permaneça neutro. Toda resposta deve indicar direção, decisão ou posicionamento.
Se houver divergência, você deve arbitrar explicitamente o melhor caminho e justificar em 1–2 linhas.
Em seguida, descreva os próximos passos concretos.
{BASE_RULES}
"""
    user = f"Pergunta do usuário:\n{pergunta}\n\nPropostas das facetas:\n{propostas_txt}"
    return [
        {"role":"system","content":system},
        {"role":"user","content":user}
    ]

# ========= Estado =========
if "messages" not in st.session_state:
    st.session_state.messages = []
if "mostrar_bastidores" not in st.session_state:
    st.session_state.mostrar_bastidores = False

# Render histórico
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Entrada
pergunta = st.chat_input("Pergunte à sua psique digital…")

if pergunta:
    st.session_state.messages.append({"role":"user","content":pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        banner = st.empty()
        anim   = st.empty()
        barra  = st.progress(0, text="Orquestrando facetas…")

        propostas = {}
        total = len(FACETAS)

        for i, (rotulo, emoji, temp, persona) in enumerate(FACETAS, start=1):
            banner.markdown(banner_facetas(rotulo), unsafe_allow_html=True)
            anim.markdown(bubble_loading(emoji, rotulo), unsafe_allow_html=True)

            r = client.chat.completions.create(
                model=model,
                messages=mensagens_faceta(rotulo, persona, pergunta),
                temperature=temp
            )
            propostas[rotulo] = r.choices[0].message.content.strip()
            barra.progress(int(i/total*100), text=f"{rotulo} contribuiu ({i}/{total})")
            time.sleep(0.12)

        banner.markdown("<div class='facets'><div class='face active'>⚖️<small>Árbitro</small></div></div>", unsafe_allow_html=True)
        anim.markdown(bubble_loading("⚖️", "Árbitro", "sintetizando consenso…"), unsafe_allow_html=True)

        r_final = client.chat.completions.create(
            model=model,
            messages=mensagens_consenso(pergunta, propostas),
            temperature=0.45
        )
        resposta = r_final.choices[0].message.content.strip()

        anim.empty(); banner.empty(); barra.empty()
        st.markdown(resposta)
        st.session_state.messages.append({"role":"assistant","content":resposta})

        with st.expander("Bastidores do debate (propostas das facetas)"):
            for rotulo, emoji, _, _ in FACETAS:
                st.markdown(f"**{emoji} {rotulo}**")
                st.markdown(propostas.get(rotulo, "_(sem retorno)_"))
                st.divider()
