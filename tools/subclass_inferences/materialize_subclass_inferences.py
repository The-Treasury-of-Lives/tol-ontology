"""Materialize rdfs:subClassOf inferences to help OWL-RL reasoners."""

import sys
import tempfile

from argparse import ArgumentParser

from rdflib import Graph, Namespace, BNode
from rdflib.namespace import RDFS, OWL


try:
    from owlready2 import get_ontology, default_world, sync_reasoner
except ImportError:
    sys.exit('owlready2 reasoner is not in your Python environment, please install')

def _run_reasoner(inputs: list[str], output_ttl: str, version: str):

    input_graph = Graph()
    for one_input in inputs:
        # Format will be guessed from the name suffix
        input_graph.parse(one_input)

    # Remove imports from ontology
    input_graph.remove((None, OWL.imports, None))

    # owlready2 does not accept TTL files. Convert to N-Triples.
    with tempfile.NamedTemporaryFile('w', suffix='.nt') as temp_file:
        input_graph_str = input_graph.serialize(format='nt')
        temp_file.write(input_graph_str)

        ontology = get_ontology(f'file://{temp_file.name}').load(only_local=True)

        # Run OWL DL reasoner (HermiT reasoner is used by default in owlready2).
        with ontology:
            sync_reasoner()

        raw_output_graph = Graph().parse(
            data=default_world.as_rdflib_graph().serialize(format='turtle'),
            format='turtle')

        output_graph = Graph()

        # Add subclass assertions to output graph.
        for s, p, o in raw_output_graph:
            if p == RDFS.subClassOf and not isinstance(o, BNode):
                output_graph.add((s, p, o))

        for prefix, namespace in input_graph.namespaces():
            output_graph.bind(prefix, namespace)

        output_graph.serialize(destination=output_ttl, format='turtle')

def _materialize_subclasses(argv: list[str]):
    parser = ArgumentParser(
        "Subclass Materializer",
         description="Use OWL DL reasoner to generate inferred rdfs:subClassOf triples. "
                     "Requires owlready2 to be installed in your Python environment.")
    parser.add_argument("output", action="store",
                        help="Path of output (Turtle format)")
    parser.add_argument("inputs", nargs="+", action="store",
                        help="RDF input, format inferred from file suffix.")
    parser.add_argument("-v", "--version", action="store", default="X.x.x",
                        help="Version to append to ontology URI, default X.x.x")
    args = parser.parse_args(argv)
    _run_reasoner(args.inputs, args.output, args.version)


if __name__ == '__main__':
    _materialize_subclasses(sys.argv[1:])
