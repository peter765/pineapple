import pprint
import requests
import re

from util import Events

# API-URL and type of headers sent by POST-request
api_url = "https://api.e-hentai.org/api.php"
json_request_headers = "{'content-type': 'application/json'}"

class Plugin(object):
    def __init__(self, pm):
        self.pm = pm
        self.name = "Exhentai"

    @staticmethod
    def register_events():
        return [Events.Message("Exhentai")]

    @staticmethod
    def return_unique_set(iterable, key=None):
        # taken from unique_everseen instead of importing an extra dependency

        seenset = set()
        seenset_add = seenset.add
        seenlist = []
        seenlist_add = seenlist.append
        if key is None:
            for element in iterable:
                try:
                    if element not in seenset:
                        seenset_add(element)
                        yield element
                except TypeError as e:
                    if element not in seenlist:
                        seenlist_add(element)
                        yield element
        else:
            for element in iterable:
                k = key(element)
                try:
                    if k not in seenset:
                        seenset_add(k)
                        yield element
                except TypeError as e:
                    if k not in seenlist:
                        seenlist_add(k)
                        yield element
        return seenlist

    async def handle_message(self, message_object):
        """
        Prints exhentai gallery info when a message contains an (average formatted) exhentai-url
        :param message_object: discord.Message object containing the message
        """

        # RegEx for finding all exhentai-links formatted like copied from exhentai adressbar
        # maybe broaden it up to match e-hentai / http / written www if still good performance-wise
        # possible id is a positive integer and possible token is a 10digit hex string
        regex_result_list = re.findall(r'(https://exhentai.org/g/([0-9]+)/([0-9a-f]{10})/)', message_object.content)
        regex_result_list_unique = list(tuple(self.return_unique_set(regex_result_list)))

        for link_tuple in regex_result_list_unique:

            # Setting the 2nd last and last tuple value of the RegEx to properly named variables.
            # the regex_result_list contains of a tuple with the different substrings in it
            # link_tuple[0] is the whole string, link_tuple[n] are the regex matches

            gallery_id = link_tuple[-2]
            gallery_token = link_tuple[-1]

            # create json from POST-response using requests built-in parser
            json_data = requests.post(api_url, self.build_payload(gallery_id, gallery_token),
                                      json_request_headers).json()

            if not 'error' in json_data['gmetadata'][0]:

                # Build the title-message


                await self.pm.clientWrap.send_message(self.name, message_object.channel, self.build_title_string(
                    json_data) + "\n" + self.build_title_jpn_string(json_data) + "\n")

                # Send the cover as its own String (non-embed) for preview
                await self.pm.client.send_message(message_object.channel, json_data['gmetadata'][0]['thumb'])

                # print message including tag-section
                await self.pm.clientWrap.send_message(self.name, message_object.channel,
                                                      self.build_tag_section(json_data) + "\n")


    @staticmethod
    def build_payload(gallery_id, gallery_token):
        return '{"method": "gdata","gidlist": [[' + gallery_id + ',"' + gallery_token + '"]],"namespace": 1}'

    @staticmethod
    def build_title_string(json_data):
        return 'Title: ' + pprint.pformat(json_data['gmetadata'][0]['title'])

    @staticmethod
    def build_title_jpn_string(json_data):
        if json_data['gmetadata'][0]['title_jpn']:
            return 'Japanese Title: ' + pprint.pformat(json_data['gmetadata'][0]['title_jpn'])
        return ""

    # TODO: (core) Make the taglist look pretty when printed
    @staticmethod
    def build_tag_section(json_data):
        # ", " is the line separator. Tags (eg. "female:schoolgirl") will be added spaces around the ":"
        return (", ".join(json_data['gmetadata'][0]['tags'])).replace(":", " : ")
