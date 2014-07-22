#!/usr/bin/env python
'''Test that NIDM-Results examples are consistent with nidm-results.owl

@author: Camille Maumet <c.m.j.maumet@warwick.ac.uk>, Satrajit Ghosh
@copyright: University of Warwick 2014
'''
import unittest
import os
# from subprocess import call #jb: call not used 
import re
import rdflib

from rdflib.graph import Graph
from TestCommons import *
from CheckConsistency import *

RELPATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class TestExamples(unittest.TestCase):

    def setUp(self):
        # Retreive owl file for NIDM-Results
        owl_file = os.path.join(RELPATH, 'nidm-results.owl')
        # check the file exists
        assert os.path.exists(owl_file)
        # Read owl (turtle) file
        self.owl = Graph()

        # This is a workaround to avoid issue with "#" in base prefix as 
        # described in https://github.com/RDFLib/rdflib/issues/379,
        # When the fix is introduced in rdflib these 2 lines will be replaced by:
        # self.owl.parse(owl_file, format='turtle')
        owl_txt = open(owl_file, 'r').read().replace("http://www.w3.org/2002/07/owl#", 
                        "http://www.w3.org/2002/07/owl")
        self.owl.parse(data=owl_txt, format='turtle')
        
        # Retreive all classes defined in the owl file
        self.sub_types = get_class_names_in_owl(self.owl) #set(); #{'entity': set(), 'activity': set(), 'agent' : set()}
        # For each class find out attribute list as defined by domain in attributes
        # For each ObjectProperty found out corresponding range
        attributes_ranges = get_attributes_from_owl(self.owl)
        self.attributes = attributes_ranges[0]
        self.ranges = attributes_ranges[1]      

        self.examples = dict()
        for example_file in example_filenames:
<<<<<<< HEAD
            provn_file = os.path.join(os.path.dirname(os.path.dirname(
                                os.path.abspath(__file__))), example_file)
            ttl_file_url = get_turtle(provn_file)
=======

            # If True turtle file will be downloaded from the prov store using
            # the address specified in the README.  If False the turtle version
            # will be retrieved on the fly using the prov translator. By
            # default set to True to check as README should be up to date but
            # setting to False can be useful for local testing.
            ttl_from_readme = False

            if ttl_from_readme:
                # Get URL of turtle from README file
                readme_file = os.path.join(RELPATH, 
                                           os.path.dirname(example_file), 'README')
                with open(readme_file, 'r') as readme_file:
                    readme_txt = readme_file.read()
                    turtle_search = re.compile(r'.*turtle: (?P<ttl_file>.*\.ttl).*')
                    extracted_data = turtle_search.search(readme_txt) 
                    ttl_file_url = extracted_data.group('ttl_file');
            else:
                # Find corresponding provn file
                provn_file = os.path.join(RELPATH, example_file)
                provn_file = open(provn_file, 'r')
                ex_provn = provn_file.read()

                url = "https://provenance.ecs.soton.ac.uk/validator/provapi/documents/"
                headers = { 'Content-type' : "text/provenance-notation",
                            'Accept' : "text/turtle" }
                req = urllib2.Request(url, ex_provn, headers)
                response = urllib2.urlopen(req)
                ttl_file_url = response.geturl()
>>>>>>> Test based on instant conversion

            # Read turtle
            self.examples[example_file] = Graph()
            self.examples[example_file].parse(ttl_file_url, format='turtle')

    def test_check_classes(self):
        my_exception = dict()
        for example_name, example_graph in self.examples.items():
            # Check that all entity, activity, agent are defined in the data model
            exception_msg = check_class_names(example_graph, example_name, class_names=self.sub_types)
            my_exception = dict(my_exception.items() + exception_msg.items())

        # Aggredate errors over examples for conciseness
        if my_exception:
            error_msg = ""
            for unrecognised_class_name, examples in my_exception.items():
                error_msg += unrecognised_class_name+" (from "+', '.join(examples)+")"
            raise Exception(error_msg)

    def test_check_attributes(self):
        my_exception = dict()
        my_range_exception = dict()
        for example_name, example_graph in self.examples.items():
<<<<<<< HEAD
            exception_msg = check_attributes(example_graph, example_name, 
                self.attributes, self.ranges)
            my_exception = dict(my_exception.items() + exception_msg[0].items())
            my_range_exception = dict(my_range_exception.items() + exception_msg[1].items())
=======
            # Find all attributes
            for s,p,o in example_graph.triples((None, None, None)):
                # To be a DataTypeProperty then o must be a literal
                # if isinstance(o, rdflib.term.Literal):
                if p not in self.common_attributes:
                    # *** Check domain
                    # Get all defined types of current object
                    found_attributes = False
                    class_names = ""
                    for class_name in sorted(example_graph.objects(s, RDF['type'])):

                        attributes = self.attributes.get(class_name)

                        # If the current class was defined in the owl file check if current
                        # attribute was also defined.
                        if attributes:
                            if p in attributes:
                                found_attributes = True

                        class_names += ", "+example_graph.qname(class_name)

                    # if not found_attributes:
                        # if attributes:
                            # if not (p in attributes):
                    if not found_attributes:
                        key = example_graph.qname(p)+" in "+class_names[2:]
                        if not key in my_exception:
                            my_exception[key] = set([example_name])
                        else:
                            my_exception[key].add(example_name)

                    # *** Check range
                    if isinstance(o, rdflib.term.URIRef):
                        # An ObjectProperty can point to an instance, then we look for its type:
                        found_range = set(example_graph.objects(o, RDF['type']))
                        # An ObjectProperty can point to a term
                        if not found_range:
                            found_range = set([o])

                        correct_range = False
                        if p in self.range:                            
                            # If none of the class found for current ObjectProperty value is part of the range
                            # throw an error
                            if found_range.intersection(self.range[p]):
                                correct_range = True
                        if not correct_range:
                            key = ', '.join(map(example_graph.qname, sorted(found_range)))+' for '+example_graph.qname(p)
                            if not key in my_range_exception:
                                my_range_exception[key] = set([example_name])
                            else:
                                my_range_exception[key].add(example_name)

        # Aggredate errors over examples for conciseness
        error_msg = ""
        if my_exception:
            for unrecognised_attribute, example_names in my_exception.items():
                error_msg += unrecognised_attribute+" (from "+', '.join(example_names)+")"
        if my_range_exception:
            for unrecognised_range, example_names in my_range_exception.items():
                error_msg += unrecognised_range+" (from "+', '.join(example_names)+")"
        if error_msg:
            raise Exception(error_msg)


if __name__ == '__main__':
    unittest.main()
