
import logging
logger = logging.getLogger(__name__)


class Source:

    def __init__(self, args):
        logger.info("Initializing Traffic Source")

        if args.job == 'WordCount':
            self.source_file = open('src/data/WordCountData.txt', 'r')



    def get_next_message(self):
        line = self.source_file.readline()
        if ("" == line):
            logger.info("End of Source File, closing and re-opening")
            self.source_file.close()
            self.source_file = open('src/data/WordCountData.txt', 'r')
            line = self.source_file.readline()

        return line


