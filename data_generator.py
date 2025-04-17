# The point of this file is to generate metadata for a given adapter class
# Let me just try something dumb for startes

from lorem_text import lorem
import random


def generateGen3SampleMetadata():
    # I'm just gonna make a dictionar`y that is like some of the sample data
    sample_metadata = {}
    sample_metadata["_guid_type"] = "discovery_metadata"

    # insert random text wherever random is written

    gen3_discovery = {}
    # Might want to make this one into a link or something
    gen3_discovery["link"] = "https://" + lorem.words(1) + "." + lorem.words(1) + ".com/" + lorem.words(1)
    gen3_discovery["tags"] = [{}]
    gen3_discovery["tags"][0]["name"] = lorem.words(1)
    gen3_discovery["tags"][0]["category"] = lorem.words(1)
    gen3_discovery["authz"] = lorem.words(1)
    gen3_discovery["source"] = lorem.words(1)
    gen3_discovery["full_name"] = lorem.words(2)

    manifest = []
    fake_commons_url = "https://" + lorem.words(1) + "." + lorem.words(1) + ".com/" + lorem.words(1)
    for i in range(0, random.randint(1, 10)):
        manifest_entry = {}
        manifest_entry["md5sum"] = lorem.words(1)
        manifest_entry["file_name"] = lorem.words(1)
        manifest_entry["file_size"] = random.randint(1000, 100000)
        manifest_entry["object_id"] = lorem.words(1)
        manifest_entry["commons_url"] = fake_commons_url
        manifest.append(manifest_entry)

    gen3_discovery["__manifest"] = manifest
    gen3_discovery["_unique_id"] = lorem.words(1) + "_" + lorem.words(1) + "_" + lorem.words(1)
    gen3_discovery["project_id"] = lorem.words(1)
    gen3_discovery["study_description"] = lorem.paragraph()

    sample_metadata["gen3_discovery"] = gen3_discovery

    return sample_metadata

# print(generateGen3SampleMetadata())