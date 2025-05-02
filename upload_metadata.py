# import gen3.auth
# import gen3.metadata
# from data_generator import *
# import inspect

# # signature = inspect.signature(gen3.auth.Gen3Auth.__init__)

# # for param in signature.parameters.values():
# #     print(param)

# auth_1 = gen3.auth.Gen3Auth(endpoint="https://data-instance-1.dev.planx-pla.net", refresh_file="./data-instance-1.json")
# auth_2 = gen3.auth.Gen3Auth(endpoint="https://data-instance-2.dev.planx-pla.net", refresh_file="./data-instance-2.json")

# # print(auth.get_access_token())

# metadata_1 = gen3.metadata.Gen3Metadata(auth_1)
# metadata_2 = gen3.metadata.Gen3Metadata(auth_2)

# # sample_metadata = {"_guid_type":"discovery_metadata","gen3_discovery":{"link":"https://www.genome.gov/27528684/1000-genomes-project","tags":[{"name":"Aligned Reads","category":"Condition"}],"authz":"/programs/OpenAccess/projects/1000_Genomes_Project","source":"1000 Genomes Project","commons":"Open Access Data Commons","funding":"","summary":"The 1000 Genomes Project is a collaboration among research groups in the US, UK, and China and Germany to produce an extensive catalog of human genetic variation that will support future medical research studies. It will extend the data from the International HapMap Project, which created a resource that has been used to find more than 100 regions of the genome that are associated with common human diseases such as coronary artery disease and diabetes. The goal of the 1000 Genomes Project is to provide a resource of almost all variants, including SNPs and structural variants, and their haplotype contexts. This resource will allow genome-wide association studies to focus on almost all variants that exist in regions found to be associated with disease. The genomes of over 1000 unidentified individuals from around the world will be sequenced using next generation sequencing technologies. The results of the study will be publicly accessible to researchers worldwide.","study_id":"1000_Genomes_Project","full_name":"1000 Genomes Project","study_url":"https://www.genome.gov/27528684/1000-genomes-project","__manifest":[{"md5sum":"e1e56e29efad64c002e5e9749f85350f","file_name":"ALL.chrY.phase3_integrated_v2b.20130502.genotypes.vcf.gz","file_size":5656911,"object_id":"dg.OADC/60afa140-d2ab-4e32-bf73-40bf48787655","commons_url":"gen3.datacommons.io/"},{"md5sum":"b405180c1328a0fc93b668fa4d24c302","file_name":"ALL.chrY.phase3_integrated_v2b.20130502.genotypes.vcf.gz.tbi","file_size":8077,"object_id":"dg.OADC/fded0c2c-8a18-413f-91e2-f132853ed91a","commons_url":"gen3.datacommons.io/"},{"md5sum":"09158d4beeb679fa70a7cabd3fc504a5","file_name":"igsr_populations.tsv","file_size":30970,"object_id":"dg.OADC/9baeeb42-563f-47fe-87f7-a6ae17fc3d20","commons_url":"gen3.datacommons.io/"},{"md5sum":"435bbcd5f4b6e2ce2d07dbba4910b2ca","file_name":"integrated_call_samples_v3.20200731.ALL.ped","file_size":209431,"object_id":"dg.OADC/096880f8-07e4-4a76-ba53-b4b6402d4dc3","commons_url":"gen3.datacommons.io/"}],"_unique_id":"1000_Genomes_Project","project_id":"OpenAccess-1000_Genomes_Project","short_name":"OpenAccess-1000_Genomes_Project","commons_url":"https://gen3.datacommons.io","study_title":"1000 Genomes Project","subjects_count":0,"_subjects_count":0,"accession_number":"1000_Genomes_Project","data_files_count":4,"study_description":"The 1000 Genomes Project is a collaboration among research groups in the US, UK, and China and Germany to produce an extensive catalog of human genetic variation that will support future medical research studies. It will extend the data from the International HapMap Project, which created a resource that has been used to find more than 100 regions of the genome that are associated with common human diseases such as coronary artery disease and diabetes. The goal of the 1000 Genomes Project is to provide a resource of almost all variants, including SNPs and structural variants, and their haplotype contexts. This resource will allow genome-wide association studies to focus on almost all variants that exist in regions found to be associated with disease. The genomes of over 1000 unidentified individuals from around the world will be sequenced using next generation sequencing technologies. The results of the study will be publicly accessible to researchers worldwide.","data_download_links":[{"guid":"dg.OADC/60afa140-d2ab-4e32-bf73-40bf48787655","title":"ALL chrY Phase3 Integrated Genotypes VCF","description":""},{"guid":"dg.OADC/fded0c2c-8a18-413f-91e2-f132853ed91a","title":"ALL chrY Phase3 Integrated Genotypes TBI","description":""},{"guid":"dg.OADC/9baeeb42-563f-47fe-87f7-a6ae17fc3d20","title":"IGSR Populations TSV","description":""},{"guid":"dg.OADC/096880f8-07e4-4a76-ba53-b4b6402d4dc3","title":"Integrated Cell Samples PED","description":""}]}}
# # print(sample_metadata["gen3_discovery"]["_unique_id"])

# # metadata.delete("1000_Genomes_Project")
# # metadata.create("1000_Genomes_Project", sample_metadata)

# for i in range(1, 11):
#     metadata = metadata_1
#     if i % 2 == 0:
#         metadata = metadata_2
#     print(i)
#     sample_metadata = generateGen3SampleMetadata()
#     print(sample_metadata["gen3_discovery"]["_unique_id"])
#     metadata.create(sample_metadata["gen3_discovery"]["_unique_id"], sample_metadata)

import gen3.auth
import gen3.metadata
from data_generator import *
import os
import sys

num_repeats = int(sys.argv[1])

refresh_token = os.popen('kubectl exec -c fence $(kubectl get pods | grep "^fence-deployment" | awk \'{print $1}\') -- fence-create token-create --scopes openid,user,fence,data,credentials,google_service_account --type access_token --exp 3600 --username test | tail -1').read().strip()
print(refresh_token)
auth = gen3.auth.Gen3Auth(endpoint="https://data-instance-3.dev.planx-pla.net", access_token=refresh_token)

#auth = gen3.auth.Gen3Auth(endpoint="https://data-instance-2.dev.planx-pla.net", refresh_file="./data-instance-2.json")
#print(auth.get_access_token())

metadata = gen3.metadata.Gen3Metadata(auth)

# sample_metadata = {"_guid_type":"discovery_metadata","gen3_discovery":{"link":"https://www.genome.gov/27528684/1000-genomes-project","tags":[{"name":"Aligned Reads","category":"Condition"}],"authz":"/programs/OpenAccess/projects/1000_Genomes_Project","source":"1000 Genomes Project","commons":"Open Access Data Commons","funding":"","summary":"The 1000 Genomes Project is a collaboration among research groups in the US, UK, and China and Germany to produce an extensive catalog of human genetic variation that will support future medical research studies. It will extend the data from the International HapMap Project, which created a resource that has been used to find more than 100 regions of the genome that are associated with common human diseases such as coronary artery disease and diabetes. The goal of the 1000 Genomes Project is to provide a resource of almost all variants, including SNPs and structural variants, and their haplotype contexts. This resource will allow genome-wide association studies to focus on almost all variants that exist in regions found to be associated with disease. The genomes of over 1000 unidentified individuals from around the world will be sequenced using next generation sequencing technologies. The results of the study will be publicly accessible to researchers worldwide.","study_id":"1000_Genomes_Project","full_name":"1000 Genomes Project","study_url":"https://www.genome.gov/27528684/1000-genomes-project","__manifest":[{"md5sum":"e1e56e29efad64c002e5e9749f85350f","file_name":"ALL.chrY.phase3_integrated_v2b.20130502.genotypes.vcf.gz","file_size":5656911,"object_id":"dg.OADC/60afa140-d2ab-4e32-bf73-40bf48787655","commons_url":"gen3.datacommons.io/"},{"md5sum":"b405180c1328a0fc93b668fa4d24c302","file_name":"ALL.chrY.phase3_integrated_v2b.20130502.genotypes.vcf.gz.tbi","file_size":8077,"object_id":"dg.OADC/fded0c2c-8a18-413f-91e2-f132853ed91a","commons_url":"gen3.datacommons.io/"},{"md5sum":"09158d4beeb679fa70a7cabd3fc504a5","file_name":"igsr_populations.tsv","file_size":30970,"object_id":"dg.OADC/9baeeb42-563f-47fe-87f7-a6ae17fc3d20","commons_url":"gen3.datacommons.io/"},{"md5sum":"435bbcd5f4b6e2ce2d07dbba4910b2ca","file_name":"integrated_call_samples_v3.20200731.ALL.ped","file_size":209431,"object_id":"dg.OADC/096880f8-07e4-4a76-ba53-b4b6402d4dc3","commons_url":"gen3.datacommons.io/"}],"_unique_id":"1000_Genomes_Project","project_id":"OpenAccess-1000_Genomes_Project","short_name":"OpenAccess-1000_Genomes_Project","commons_url":"https://gen3.datacommons.io","study_title":"1000 Genomes Project","subjects_count":0,"_subjects_count":0,"accession_number":"1000_Genomes_Project","data_files_count":4,"study_description":"The 1000 Genomes Project is a collaboration among research groups in the US, UK, and China and Germany to produce an extensive catalog of human genetic variation that will support future medical research studies. It will extend the data from the International HapMap Project, which created a resource that has been used to find more than 100 regions of the genome that are associated with common human diseases such as coronary artery disease and diabetes. The goal of the 1000 Genomes Project is to provide a resource of almost all variants, including SNPs and structural variants, and their haplotype contexts. This resource will allow genome-wide association studies to focus on almost all variants that exist in regions found to be associated with disease. The genomes of over 1000 unidentified individuals from around the world will be sequenced using next generation sequencing technologies. The results of the study will be publicly accessible to researchers worldwide.","data_download_links":[{"guid":"dg.OADC/60afa140-d2ab-4e32-bf73-40bf48787655","title":"ALL chrY Phase3 Integrated Genotypes VCF","description":""},{"guid":"dg.OADC/fded0c2c-8a18-413f-91e2-f132853ed91a","title":"ALL chrY Phase3 Integrated Genotypes TBI","description":""},{"guid":"dg.OADC/9baeeb42-563f-47fe-87f7-a6ae17fc3d20","title":"IGSR Populations TSV","description":""},{"guid":"dg.OADC/096880f8-07e4-4a76-ba53-b4b6402d4dc3","title":"Integrated Cell Samples PED","description":""}]}}
# print(sample_metadata["gen3_discovery"]["_unique_id"])

# metadata.delete("1000_Genomes_Project")
# metadata.create("1000_Genomes_Project", sample_metadata)

for i in range (1, num_repeats+1):
        if i % 10 == 0:
                print(i)
        sample_metadata = generateGen3SampleMetadata()
        metadata.create(sample_metadata["gen3_discovery"]["_unique_id"], sample_metadata)
