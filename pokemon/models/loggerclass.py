import sys
import traceback

class logger:

    def error(self, excInfo=None, msg="", verbose=True):
        """ prints out error messages """
        errorMsg = '' 
        # Process the excInfo
        if excInfo:
            exc_type, exc_value, exc_traceback = excInfo										
            errorMsg = exc_value			
            errorMsg = '%s\nType:%s' % (errorMsg, str(exc_type).replace("<type '", "").replace("'>", "")	)
            formattedError = traceback.format_exception(exc_type, exc_value, exc_traceback)														
            for x in range (1, len(formattedError) -1):
                if formattedError[x].strip()[-12:] == ' in <module>':					
                    errorMsg = '%s\n%s' % (errorMsg, formattedError[x].strip()[:-12])
                else:
                    errorMsg = '%s\n%s' % (errorMsg, formattedError[x].strip())									
            
        # Add custom message
        if msg:
            if errorMsg:
                errorMsg = '%s\nMessage:%s' % (errorMsg, msg)
            else:	
                errorMsg = msg						
        
        if verbose:
            print(errorMsg)

        return errorMsg 

