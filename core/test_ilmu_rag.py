"""E2E test — RAG + ILMU LLM."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.env_loader import load_env
load_env()

from core.rag import RAG
from core.ilmu_llm import IlmuLLM


def main():
    print("1. Init IlmuLLM...")
    llm = IlmuLLM()
    print(f"   model: {llm.model}")

    print("\n2. Init RAG with IlmuLLM...")
    rag = RAG(llm=llm)
    print("   ok")

    q = "Apa itu Gen Z Malaysia?"
    print(f"\n3. rag.search({q!r})...")
    result = rag.search(q, synthesize=True)

    print(f"\n   Answer:\n   {result.answer}")

    u = llm.last_usage
    p_rm, c_rm = llm.cost_estimate()
    print(f"\n   Tokens: in={u.get('prompt_tokens',0)} out={u.get('completion_tokens',0)}")
    print(f"   Cost:   RM{p_rm + c_rm:.6f}")

    rag.close()
    print("\ndone.")


if __name__ == "__main__":
    main()