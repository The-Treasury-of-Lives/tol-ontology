from pathlib import Path
import logging
from rdflib import Graph, ConjunctiveGraph
from rdflib.query import Result
from rdflib.plugins.parsers.notation3 import BadSyntax
import argparse
from prettytable import PrettyTable

logger = logging.getLogger("")

def print_result(result: Result):

    table = PrettyTable(["Undefined Concept", "Referenced In"], align = "l")
    for row in result:
        table.add_row([row["iri"], row["graph"]])
    if len(result):
        print(table)
    else:
        print("Good news: no undefined concepts found!")

def run_query(graph: Graph) -> Result :

    query = """
        SELECT DISTINCT ?iri ?graph
        WHERE
        {
            {GRAPH ?graph { ?s ?iri ?o }}
            UNION
            {GRAPH ?graph { ?s ?p ?iri }}
            UNION
            {GRAPH ?graph { ?iri ?p ?o }}

            FILTER(!CONTAINS(STR(?iri), "DoNotValidate"))
            # Parameterize this so the script is ontology-agnostic
            FILTER (REGEX(STR(?iri), "/ns/ontology/tol/.") || REGEX(STR(?iri), "/ns/ontology/gist/."))
            FILTER NOT EXISTS { ?iri a ?type }
        }
        ORDER BY ?graph ?iri
    """

    return graph.query(query)

def add_named_graph(path: Path, conjunctive_graph: ConjunctiveGraph):

    file = str(path)
    named_graph = conjunctive_graph.get_context(path.name)
    try:
      named_graph.parse(file)
    except BadSyntax as syntaxError:
      logging.error(f"Bad syntax in file: '{file}'\nError: '{syntaxError}'")
      print(f"Skipped '{file}', bad syntax.")
    except:
      logging.error(f"Unknown error while processing: '{file}'")
      print(f"Skipped '{file}', unknown error.")

def get_conjunctive_graph(file_list: list) -> ConjunctiveGraph:

    conjunctive_graph = ConjunctiveGraph()

    for file in file_list:
        path = Path(file)
        if not path.exists():
            logger.warning(f"{file} does not exist. Ignoring.")
        elif path.is_dir():
            for item in path.glob("*.ttl"):
                logger.debug(f"Loading {item} into the combined graph")
                add_named_graph(Path(item), conjunctive_graph)
        elif path.is_file():
            add_named_graph(Path(file), conjunctive_graph)

    # conjunctive_graph.serialize("cg.trig", format="trig")
    return conjunctive_graph

def get_arg_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        prog="Find Undefined Concepts",
        description="Finds ontology concepts that are used but not defined in a set of Turtle files.'Undefined' concepts have not been assigned an rdf:type.")

    parser.add_argument("files",
                    nargs="+",
                    type=str,
                    help="Path to one or more files and/or directories containing the RDF files to be read into the graph for testing. All Turtle files in a directory are included.")

    return parser

def main():

    logging.basicConfig(level=logging.INFO)

    # Parse arguments.
    arg_parser = get_arg_parser()
    parsed_args = arg_parser.parse_args()

    # Get conjunctive graph of all files, each in its own named graph.
    conjunctive_graph = get_conjunctive_graph(parsed_args.files)

    # Run query over the conjunctive graph to find any undefined concepts.
    result = run_query(conjunctive_graph)

    # Output the query result as a table.
    print_result(result)


if __name__ == "__main__":
    main()
