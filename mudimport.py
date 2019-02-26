'''
Module that deserializes developer-made game-data, converting it into real objects
'''
import json
import os
import importlib
import traceback
from location import Location, Exit
from util.stocstring import StocString
from util.distr import RandDist

def get_filenames(directory, ext=""):
    '''returns all filenames in [directory] with extension [ext]'''
    return [directory + name for name in os.listdir(directory) \
            if name.endswith(ext)]

class Library:
    '''Class to represent a library of interacting game elements'''
    def __init__(self):
        self.locations = {}
        self.char_classes = {}
        self.items = {}
        # random distribution based on class frequencies
        self.random_class = None
        self._loc_importer = LocationImporter(self.locations)
        self._char_importer = CharacterClassImporter(self.char_classes)
        self._item_importer = ItemImporter(self.items)

    def build_class_distr(self):
        '''takes the current set of CharacterClasses
        and builds a random distribution based on their frequency
        can be called again to rebuild the distribution
        '''
        # grab character classes with frequency > 0
        to_include = [c_class for c_class in self.char_classes.values() 
                     if c_class.frequency > 0]
        if len(to_include) == 0:
            raise Exception("No valid classes with frequency greater than 0")
        self.random_class = RandDist(to_include, list(map(lambda x: x.frequency, to_include)))
    
    def import_files(self, locations=[], chars=[], items=[]):
        if locations:
            for filename in locations:
                self._loc_importer.import_file(filename)
        if chars:
            for filename in chars:
                self._char_importer.import_file(filename)
        if items:
            for filename in items:
                self._item_importer.import_file(filename)
        if locations:
            pass
            #self._loc_importer.build_exits()
            #self._loc_importer.add_items()
            #self._loc_importer.add_entities()
    
    def import_results(self):
        return str(self._loc_importer) + str(self._item_importer) + str(self._char_importer)


# see if this trashes the stack trace
class ImporterException(Exception):
    def __init__(self, message, game_element):
        self.game_element = game_element
        super().__init__(message)

def process_json(filename):
    with open(filename) as location_file:
        # read the file, processing any stocstring macros
        json_data = StocString.process(location_file.read())
    json_data = json.loads(json_data)
    # all importers expect a "name" field, so check for that
    assert("name" in json_data and type(json_data["name"]) is str)
    return json_data

class Importer:
    '''Base class for other importers
    objects:        dict mapping object names -> object instances
    object_source:  dict mapping object names -> filenames
    file_data:      dict mapping filenames -> filedata
    file_fails:     dict mapping filenames -> reasons while file failed to load
    failures:       dict mapping object names -> reasons why they could not be constructed
    '''
    def __init__(self, lib={}):
        self.objects = lib
        self.object_source = {}
        self.file_data = {}
        self.file_fails = {}
        self.failures = {}
    
    def import_file(self, filename):
        '''Import one file with filename [filename]'''
        try:
            json_data = process_json(filename)
            self.file_data[filename] = json_data
        except Exception as ex:
            self.file_fails[filename] = traceback.format_exc()
            return
        try:
            name, game_object = self._do_import(json_data)
            self.objects[name] = game_object
            self.object_source[name] = filename
        except Exception as ex:
            self.failures[ex.name] = traceback.format_exc()

    def _do_import(self, json_data):
        '''This method should be implemented in base classes'''
        pass

    def __str__(self):
        '''cheap method to get an output for all values in each list'''
        output = "\nSUCCESS LIST\n"
        for _, obj in self.objects.items():
            output += str(obj) + "\n"
        output += "FAILURE LIST\n"
        for name, reason in self.failures.items():
            output += str(name) + " :\n"
            output += str(reason) + "\n"
        return output


class LocationImporter(Importer):
    '''Imports Locations from json'''
    def __init__(self, lib={}):
        self.exit_failures = {}
        self.item_failures = {}
        super().__init__(lib)

    def _do_import(self, json_data):
        try:
            name = json_data["name"]
            # check that "items" is a dict
            if "items" in json_data:
                assert(isinstance(json_data["items"], dict))
            # check that "exits" is a list
            if "exits" in json_data:
                assert(isinstance(json_data["exits"], list))
        except Exception as ex:
            # modify exception to show what the name is, rethrow
            setattr(ex, "name", name)
            raise ex
        return name, Location(json_data["name"], json_data["description"])

    #TODO: delete all existing exits
    def build_exits(self):
        '''looks at the skeletons, adds exits for each
        on fail, an exit is simply not added'''
        pass
#        for location_name, skeleton in self.skeletons.items():
#            # creating an empty list of failed exits
#            self.exit_failures[location_name] = {}
#            if "exits" not in skeleton:
#                continue
#            for exit in skeleton["exits"]:
#                
#                # check if the exit specified a destination first
#                if "destination" not in exit:
#                    # make a fake name
#                    exit_name = "[Exit #%i]" % (len(self.exit_failures))
#                    self.exit_failures[location_name][exit_name] = "No destination provided"
#                    continue
#                try:
#                    if exit["destination"] in self.successes:
#                        # get destination from the successfully loaded locations
#                        dest = self.successes[exit["destination"]]
#                        
#
#                        # parsing the strings in the blacklist/whitelists,
#                        if "blacklist" in exit:
#                            exit["blacklist"] = [library.character_classes[clsname]
#                                                 for clsname in exit["blacklist"]]
#                        if "whitelist" in exit:
#                            exit["whitelist"] = [library.character_classes[clsname]
#                                                 for clsname in exit["whitelist"]]
#
#                        # TODO: handle references to "proper characters"
#                        
#                        # Preparing exit dict for conversion to keyword arguments
#                        kwargs = dict(exit)
#                        del kwargs["destination"]
#                        #del kwargs["name"]
#                        self.successes[location_name].add_exit(Exit(dest, **kwargs))
#                    elif exit["destination"] in self.failures:
#                        raise Exception("Destination \'%s\' failed to import." % (exit["destination"]))
#                    else:
#                        raise Exception("Destination \'%s\' could not be found." % (exit["destination"]))
#                except Exception:
#                    self.exit_failures[location_name][(exit["destination"])] = traceback.format_exc()
#            # check if any failed exits were added to the exit_failures dictionary
#            # if not, we delete the entry for this location (no failures to mention!)
#            if not self.exit_failures[location_name]:
#                del self.exit_failures[location_name]
#
#    def add_items(self):
#        '''looks at the skeletons, adds items for each
#        on fail, an item is simply not added'''
#        for location_name, skeleton in self.skeletons.items():
#            failures = {}
#            # items might be provided, in which case we just continue
#            if "items" not in skeleton:
#                continue
#            for item_name, quantity in skeleton["items"].items():
#                try:
#                    item = library.items[item_name]
#                    quanity = int(quantity)
#                    self.successes[location_name].add_items(item, quanity)
#                except Exception as ex:
#                    failures[item_name] = traceback.format_exc()
#                    # this is an idempotent operation
#                    # even if we re-assign the dict multiple times, it has the same effect
#                    self.item_failures[location_name] = failures
#
#    def add_entities(self):
#        '''looks at skeletons, adds entity for each
#        on fail, an entity is simply not added'''
#        # entities have not been added yet
#        pass

    def all_to_str(self):
        output = super().all_to_str()
        output += "\nEXIT FAILURES\n"
        for location, exits in self.exit_failures.items():
            for dest, exc in exits.items():
                output += str(location) + " -> " + str(dest) + "\n" + exc
        output += "\nITEM FAILURES\n"
        for location, items in self.exit_failures.items():
            output += str(location) + ":\n"
            for item, exc in exits.items():
                output +=  str(dest) + "\n" + exc
        return output


class CharacterClassImporter(Importer):
    '''Importer for CharacterClasses'''
    def _do_import(self, json_data):
        try:
            name = json_data["name"]
            path = json_data["path"]
            module = importlib.import_module(path.replace('.py', '').replace('/', '.'))
            character_class = getattr(module, name)
            # add this field back when it makes sense
            # if "starting_location" in json_data:
            #    starting_location = self.locations[json_data["starting_location"]]
            #    character_class.starting_location = starting_location
            if "frequency" in json_data:
                assert isinstance(json_data["frequency"], float)
                character_class.frequency = json_data["frequency"]
            # add other json arguments here
        except Exception as ex:
            setattr(ex, "name", name)
            raise ex
        return str(character_class), character_class

class ItemImporter(Importer):
    def _do_import(self, json_data):
        try:
            name = json_data["name"]
            path = json_data["path"] 
            module = importlib.import_module(path.replace('.py', '').replace('/', '.'))
            item = getattr(module, name)
        except Exception as ex:
            setattr(ex, "name", name)
            raise ex
        return str(item), item

class EntityImporter(Importer):
    pass