"""
art_illumina -sam   -1 $profilePath/csNGSProfile_hiseq2500_1.txt
                    -2 $profilePath/csNGSProfile_hiseq2500_2.txt
                    -f 100 -l 150 -p  -m 250 -s 50 -rs $RANDOM -ss HS25 -i \$SEED -o \${INPUTBASE}_R

"""
import argparse,datetime,logging,os,sys

class NGSReads:
    def __init__(self,program,params,,logger):
        self.appLogger=logging.getLogger('sngsw')