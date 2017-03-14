import argparse,datetime,logging,os,path,sys
import numpy as np
from MELoggingFormatter import MELoggingFormatter as mlf
from NGSPhyDistribution import NGSPhyDistribution as ngsphydistro
if (sys.version_info[0:2]<(3,0)):
    import ConfigParser as cp
elif (sys.version_info>=(3,0)):
    import configparser as cp

class Settings:
    ploidy=1
    readcount=False
    ngsart=False

    def __init__(self,filename):
        # If I've got this far, then filename is a correct file
        self.path=os.path.abspath(filename)
        self.appLogger=logging.getLogger('ngsphy')
        self.appLogger.debug("(class Settings) __init__()")
        # default settings can be established.
        self.parser=cp.SafeConfigParser()
        self.parser.read(self.path)


    def checkArgs(self):
        allGood=True
        parserMessageCorrect="All parameters are correct."
        parserMessageWrong="Settings - Problem found! "
        statusGeneral,messageGeneral= self.checkSectionGeneral(parserMessageCorrect,parserMessageWrong)
        if(statusGeneral):
            if self.parser.has_section("ngs-reads-art"):
                statusNGSArt,messageNGSArt=self.checkSectionNGSReadsArt(parserMessageCorrect,parserMessageWrong)
                if (statusNGSArt):
                    ## Next check
                        statusCoverage,messageCoverage=self.checkSectionCoverage(parserMessageCorrect,parserMessageWrong)
                        if not statusCoverage:
                            return statusCoverage, messageCoverage
                else:
                    return statusNGSArt,messageNGSArt
                    # Exit here
                if self.parser.has_section("read-count"):
                    self.parser.remove_section("read-count")
                    self.appLogger.warning("[read-count] section is incompatible with [ngs-reads-art]. Omiting this section.")
            else:
                self.ngsart=False
                self.appLogger.info("Settings: No NGS generation section available")
                # readcount
                if self.parser.has_section("read-count"):
                    statusRC,messageRC=self.checkSectionReadCount(parserMessageCorrect,parserMessageWrong)
                    if statusRC:
                        statusCoverage,messageCoverage=self.checkSectionCoverage(parserMessageCorrect,parserMessageWrong)
                        if not statusCoverage:
                            return statusCoverage, messageCoverage
                    else:
                        return statusRC,messageRC
                else:
                    self.readcount=False
                    self.appLogger.info("Settings: No read-count generation section available")

                if not (self.parser.has_section("read-count") or self.parser.has_section("ngs-reads-art")):
                    if (self.parser.has_section("coverage")):self.parser.remove_section("coverage")
                    self.appLogger.info("[coverage] section is not needed when [ngs-reads-art] nor [read-count] section are available. Omiting this section.")

            self.checkSectionExecution(parserMessageCorrect,parserMessageWrong)
        else:
            return statusGeneral,messageGeneral
            # Exit here
        self.appLogger.info(self.formatSettingsMessage())
        return allGood,parserMessageCorrect

    def checkSectionGeneral(self,parserMessageCorrect,parserMessageWrong):
        # checking general parameters
        if not (self.parser.has_option("general","data_prefix") or self.parser.has_option("general","dp")):
            parserMessageWrong+="\n\t<data_prefix | dp> field is missing. This prefix correponds to the name of the file sequences that are going to be processed. Exiting."
            return False, parserMessageWrong

        if not (self.parser.has_option("general","simphy_folder") or
            self.parser.has_option("general","sf")):
            # check if option simphy_folder exist in sections
            parserMessageWrong+="\n\t<simphy_folder> field is missing."
            return False, parserMessageWrong
        else:
            # parameter is set up, now check if folder exist
            path=""
            if (self.parser.has_option("general","simphy_folder")):
                path=os.path.abspath(self.parser.get("general","simphy_folder"))
            if (self.parser.has_option("general","sf")):
                path=os.path.abspath(self.parser.get("general","sf"))
                self.parser.set("general","simphy_folder",path)
                self.parser.remove_option("general","sf")

            if (os.path.exists(path) and os.path.isdir(path)):
                self.appLogger.debug("SimPhy project folder exists")
            else:
                parserMessageWrong+="\n\tSimPhy project folder does not exist, or the given path does not belong to a directory. Exiting."
                return False, parserMessageWrong

            # checking ploidy for the output data
            if (not self.parser.has_option("general","ploidy")):
                self.ploidy=1
            else:
                p=self.parser.getint("general","ploidy")
                if (p>0 and p<=2):  self.ploidy=p
                elif (p<0): self.ploidy=1
                else:   self.ploidy=2

            # Checking output folder information
            currentRun=""
            if(self.parser.has_option("general","output_folder_name")):
                currentRun=self.parser.get("general","output_folder_name")
            elif (self.parser.has_option("general","ofn")):
                currentRun=self.parser.get("general","ofn")
                self.parser.set("general","output_folder_name",currentRun)
                self.parser.remove_option("general","ofn")
            else:
                currentRun="output"

            if os.path.exists("{0}/{1}".format(path,currentRun)):
                listdir=os.listdir(path)
                counter=0
                for item in listdir:
                    if currentRun in item:
                        counter+=1
                if not counter == 0:
                    currentRun="output_{0}".format(counter+1)
            self.parser.set("general","output_folder_name","{0}/{1}".format(path,currentRun))

        return True,parserMessageCorrect

    def checkSectionNGSReadsArt(self,parserMessageCorrect,parserMessageWrong):
        ########################################################################
        # BLOCK: NGS-READS-ART
        ########################################################################
        # Checking art parameters.
        self.ngsart=True
        self.appLogger.info("NGS-reads-ART option selected.")
        # checking program dependencies
        stream = os.popen('which art_illumina').read()[0:-1]
        self.appLogger.info("Checking dependencies...")
        if stream:
            self.appLogger.info("art_illumina - Found running in: {}".format(stream))
            # Coverage parameters
            if self.parser.has_option("ngs-reads-art","o"):self.parser.remove_option("ngs-reads-art","o")
            if self.parser.has_option("ngs-reads-art","out"):self.parser.remove_option("ngs-reads-art","out")
            if self.parser.has_option("ngs-reads-art","i"):self.parser.remove_option("ngs-reads-art","i")
            if self.parser.has_option("ngs-reads-art","in"):self.parser.remove_option("ngs-reads-art","in")
            self.appLogger.warning("Removing I/O options. Be aware: I/O naming is auto-generated from SimPhy and Mating parameters.")
            # Coverage parameters
            if (self.parser.has_option("ngs-reads-art","fcov")): self.parser.remove_option("ngs-reads-art","fcov")
            if (self.parser.has_option("ngs-reads-art","f")): self.parser.remove_option("ngs-reads-art","f")
            if (self.parser.has_option("ngs-reads-art","rcount")): self.parser.remove_option("ngs-reads-art","rcount")
            if (self.parser.has_option("ngs-reads-art","c")): self.parser.remove_option("ngs-reads-art","c")

            self.appLogger.warning("Removing ART coverage options. Coverage is calculated with the [coverage] section (experimentCoverage and individualCoverage options).")
        else:
            parserMessageWrong+="art_illumina not found. Program either not installed or not in your current path. Please verify the installation. Exiting."
            return False, parserMessageWrong
        return True, parserMessageCorrect

    def checkSectionReadCount(self,parserMessageCorrect,parserMessageWrong):
        ########################################################################
        # BLOCK: READ COUNT
        ########################################################################
        # experimentCoverage /expCov
        # individualCoverage /indCov
        message=parserMessageCorrect
        if (self.parser.has_section("read-count")):
            self.readcount=True
            if not self.parser.has_option("read-count", "error"):
                self.appLogger.warning("[read-count] section. Sequencing error rate for this run is being considered as 0.")
                self.parser.set("read-count", "error","0")
            if not self.parser.has_option("read-count","reference"):
                self.appLogger.warning("[read-count] section. Using default references.")
                self.parser.set("read-count", "reference","None")
        else:
            # No read-count section
            self.readcount=False
            message="[read-count] section. Not available."

        return self.readcount,message

    ########################################################################
    # BLOCK: Coverage
    ########################################################################
    def checkSectionCoverage(self,parserMessageCorrect,parserMessageWrong):
        distro=None
        message=parserMessageCorrect
        if(self.parser.has_section("coverage")):
            if (self.parser.has_option("coverage","expCov")):
                value=self.parser.get("coverage","expCov")
                self.parser.set("coverage","experimentCoverage",value.lower())
                self.parser.remove_option("coverage","expCov")
            elif (self.parser.has_option("coverage","experimentCoverage")):
                value=self.parser.get("coverage","experimentCoverage")
                self.parser.set("coverage","experimentCoverage",value.lower())
            else:
                # parsear distribution
                parserMessageWrong+="Coverage section | Experiment Coverage distribution variable is required. Please verify. Exiting."
                return False,parserMessageWrong
            distro=ngsphydistro(0,self.parser.get("coverage","experimentCoverage"))
            check,mess=distro.checkDistribution()
            if not (check):
                parserMessageWrong+=mess
                return check,parserMessageWrong
            distro=None
            # If i got here I have EXPERIMET COVERAGE DISTRIBUTION
            if (self.parser.has_option("coverage","individualCoverage") or (self.parser.has_option("coverage","indCov"))):
                if (self.parser.has_option("coverage","indCov")):
                    value=self.parser.get("coverage","indCov")
                    self.parser.set("coverage","individualCoverage",value.lower())
                    self.parser.remove_option("coverage","indCov")
                if (self.parser.has_option("coverage","individualCoverage")):
                    value=self.parser.get("coverage","individualCoverage")
                    self.parser.set("coverage","individualCoverage",value.lower())
                distro=ngsphydistro(1,self.parser.get("coverage","individualCoverage"))
                check,mess=distro.checkDistribution()
                if not (check):
                    parserMessageWrong+=mess
                    return check,parserMessageWrong
                distro=None
            else:
                if (self.parser.has_option("coverage","locusCoverage") or (self.parser.has_option("coverage","locCov"))):
                    if (self.parser.has_option("coverage","locCov")):
                        self.parser.remove_option("coverage","locCov")
                    if (self.parser.has_option("coverage","locusCoverage")):
                        self.parser.remove_option("coverage","locusCoverage")
                    self.appLogger.warning("Locus-wise coverage option is being removed because it depends on Individual-wise coverage option, and is missing.")

            # If i got here I have EXPERIMENT COVERAGE DISTRIBUTION,
            # if i hae EXPERIMENT COVERAGE but NO INDIVIDUAL COVERAGE, then' there's no problem, i wont have locCoverage either
            # it will have been removed
            # I can keep going with the coverage loc validation
            if (self.parser.has_option("coverage","locusCoverage") or (self.parser.has_option("coverage","locCov"))):
                if (self.parser.has_option("coverage","locCov")):
                    value=self.parser.get("coverage","locCov")
                    self.parser.set("coverage","locusCoverage",value.lower())
                    self.parser.remove_option("coverage","locCov")
                if (self.parser.has_option("coverage","locusCoverage")):
                    value=self.parser.get("coverage","locusCoverage")
                    self.parser.set("coverage","locusCoverage",value.lower())
                distro=ngsphydistro(2,self.parser.get("coverage","locusCoverage"))
                check,mess=distro.checkDistribution()
                if not (check):
                    parserMessageWrong+=mess
                    return check,parserMessageWrong
                distro=None

            else:
                if (self.parser.has_option("coverage","individualCoverage")):
                    self.appLogger.info("Using Experiment- and Individual-wise coverage.")
                else:
                    self.appLogger.info("Using only Experiment-wise coverage.")
        else:
            # No coverage section
            message="Settings: Coverage section | When using [ngs-reads-art] or [read-count] section. Coverage is required. Please verify. Exiting."
            return False,message

        return True, message

    def checkSectionExecution(self,parserMessageCorrect,parserMessageWrong):
        ########################################################################
        # BLOCK: Execution
        ########################################################################
        if not self.parser.has_section("execution"):
            self.appLogger.warning("Settings - Execution block: This block has been automatically generated.")
            self.parser.add_section("execution")
            self.parser.set("execution", "environment","bash")
            self.parser.set("execution", "run","off")
            self.parser.set("execution", "threads","1")
        else:
            ####################################################################
            # OPTION: Environment
            if (self.parser.has_option("execution","env")):
                # got the short name
                value=self.parser.get("execution","env")
                self.parser.set("execution","environment",value.lower())
                self.parser.remove_option("execution","environment")
            elif (self.parser.has_option("execution","environment")):
                # got the long name, make sure it is lowercase and within the options
                value=self.parser.get("execution","environment")
                if (value in ["sge","slurm","bash"]):
                    self.parser.set("execution","environment",value.lower())
                    if (value in ["sge","slurm"]):
                        self.parser.set("execution", "run","off")
                else:
                    message="Settings: Execution block | Evironment variable is incorrect or unavailable. Please check the settings file and rerun. Exiting."
                    return False,message
            else:
                # got no environment
                self.parser.set("execution", "environment","bash")
            ####################################################################
            # OPTION: RUN
            if (self.parser.has_option("execution","run")):
                try:
                    value=self.parser.getboolean("execution","run")
                except Exception as e:
                    self.appLogger.warning("Settings - Execution block: Run automatically set up to OFF.")
                    self.parser.set("execution","run","off")
            else:
                self.appLogger.warning("Settings - Execution block: Run automatically set up to OFF.")
                self.parser.set("execution","run","off")
            ####################################################################
            # OPTION: threads
            if (self.parser.has_option("execution","threads")):
                try:
                    self.numThreads=self.parser.getint("execution","threads")
                except Exception as e:
                    self.appLogger.warning("Settings - Execution block: Threads automatically set up to 1.")
                    self.parser.set("execution","threads","1")
                    self.numThreads=1
            else:
                self.numThreads=1
                self.appLogger.warning("Settings - Execution block: Threads automatically set up to 1.")
                self.parser.set("execution","threads","1")

    def formatSettingsMessage(self):
        message="Settings:\n"
        sections=self.parser.sections()
        for sec in sections:
            message+="\t{0}\n".format(sec)
            items=self.parser.items(sec)
            for param in items:
                message+="\t\t{0}\t:\t{1}\n".format(param[0],param[1])
        return message
