import pytest
import textwrap


def main():
    print("=" * 80)
    print("🧪 Iniciando suíte de testes do Sistema de Controle Acadêmico")
    print("=" * 80)

    # Executa pytest normalmente
    # Você pode adicionar flags aqui, ex: ["-vv"]
    ret = pytest.main([])

    print("\n" + "=" * 80)
    if ret == 0:
        print("✅ TODOS OS TESTES FORAM EXECUTADOS COM SUCESSO!\n")
        print("Resumo do que foi testado:\n")

        resumo = textwrap.dedent(
            """
            📁 tests/test_domain.py
              • Tipo: TESTES UNITÁRIOS (regras de negócio)
              • O que verifica:
                  - Cálculo da média das disciplinas (E1, E2, E3)
                  - Status da disciplina (APROVADO, REPROVADO, EM_CURSO)
                  - Funções utilitárias de data e strings (nonempty, ensure_date, to_date)

            📁 tests/test_crypto.py
              • Tipo: TESTES UNITÁRIOS (criptografia e autenticação)
              • O que verifica:
                  - Cifra de César (encrypt/decrypt)
                  - Criptografia simétrica (Fernet) em dados sensíveis
                  - Hash de senha do administrador (PBKDF2-HMAC-SHA256)
                  - Troca de senha do admin e verificação de login

            📁 tests/test_api_integration.py
              • Tipo: TESTE INTEGRADO (API completa)
              • O que verifica:
                  - Login do administrador e obtenção do token
                  - Criação de aluno
                  - Criação de disciplina para o aluno
                  - Lançamento de notas (E1, E2, E3) e cálculo da média/status
                  - Geração do boletim CSV do aluno
                  - Geração e leitura de logs, incluindo mensagem decifrada
            """
        )
        print(resumo)
        print("=" * 80)
        print("👍 A suíte de testes garante cobertura básica de domínio, segurança e API.")
        print("=" * 80)
    else:
        print("❌ Alguns testes falharam. Verifique o log acima do pytest.")
        print("=" * 80)

    return ret


if __name__ == "__main__":
    raise SystemExit(main())
