"""Test ontology extraction — ILMU bge-m3 + xgen."""
from core.env_loader import load_env
load_env()

from core.ilmu_llm import IlmuLLM
import xgen_ontology_build as xo


class IlmuLLMBig(IlmuLLM):
    """max_tokens lebih tinggi + strip markdown fence."""
    
    def generate(self, prompt, *, system='', timeout=None,
                 max_tokens=2000, temperature=0.3):
        result = super().generate(
            prompt, system=system, timeout=timeout,
            max_tokens=max_tokens, temperature=temperature
        )
        result = result.strip()
        # Strip ```json ... ```
        if result.startswith('```'):
            lines = result.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            result = '\n'.join(lines).strip()
        return result


def main():
    llm = IlmuLLMBig()
    print(f'Model: {llm.model}')
    
    docs = {
        'test1': 'OP: Gen Z lemah, Gen Z macam strawberi. R: SISPAA ni parent Millennials.',
    }
    
    print('Testing mode=llm, max_tokens=2000...')
    ont = xo.build_from_documents(docs, llm=llm, mode='llm')
    
    print()
    print('=== STATS ===')
    print(ont.stats())
    print()
    print('=== NODES ===')
    for n in ont.nodes()[:15]:
        print(f'  {n}')
    print()
    print('=== EDGES ===')
    for e in ont.edges()[:15]:
        print(f'  {e}')


if __name__ == '__main__':
    main()