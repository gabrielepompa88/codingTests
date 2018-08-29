import numpy as np
from scipy.stats import norm

class RootFinder(object):
    
    def __init__(self, accuracy=1e-8):
        
        self.accuracy = accuracy # desired tolerance (default: 10^-8)
        self.__rootFindMethod = None # method to use as root finder
        
     
    def getRootFindMethod(self):
        return self.__rootFindMethod

    def setRootFindMethod(self, rootFinderName = "dekkers"):
        
        rootFindersAvailable = {"dekkers": self.__dekkersMethod,
                                "bisection": self.__bisectionMethod}
        
        if rootFinderName in rootFindersAvailable:        
            self.__rootFindMethod = rootFindersAvailable[rootFinderName]
        else:
            raise NameError("root finder method not available")

    def __bisectionMethod(self, f, a=0, b=100):
        '''
        Simple implementation of bisection method f(c) == 0.
        
        args:
            f: the function whose root c: f(c) == 0 has to be found
            a: initial guess for the lower bound of the root  (default: 0)
            b: initial guess for the upper bound of the root (default: 1)
            (An exception will be raised for invalid guesses of a and b)
            accuracy: desired tolerance
            
        output:
            approximate root c
        '''

        if f(a) * f(b) > 0:
            return np.nan # case in which f saturates and doesn't change sign
            
        while abs(b - a) > self.accuracy:
            
            c = 0.5*(a + b)
            
            if f(c) == 0:
                return c
            
            elif f(a) * f(c) > 0:
                a = c
            else:
                b = c
        return c
    
    def __dekkersMethod(self, f, a=0, b=100):
        '''
        Implementation of the Dekker's method (also derivative free) for f(c) == 0.
        Code adapted from: https://share.cocalc.com/share/ab93d447b6728ae561bf1f9e18f0b103316d715f/Efficiency%20of%20Standard%20and%20Hybrid%20Root%20Finding%20Methods.sagews?viewer=share
    
        args:
            f: the function whose root c: f(c) == 0 has to be found
            a: initial guess for the lower bound of the root (default: 0)
            b: initial guess for the upper bound of the root (default: 1)
            
        output:
            approximate root c
        '''
        
        if f(a) * f(b) > 0:
            return np.nan # case in which f saturates and doesn't change sign
            
        fa = f(a)
        fb = f(b)
        
        # initialize our c to be a and f(a)
        c = a
        fc = fa
        
        while abs(b-a) > self.accuracy:
            
            # Perform swaps to have properly inverted signs
            if fb*fc > 0:
                c = a
                fc = fa
                
            if abs(fc) < abs(fb):
                a = b
                fa = fb
                b = c
                fb = fc
                c = a
                fc = fa
            
            # bisection
            m = 0.5*(b+c)
            
            p = (b-a)*fb
            if p >= 0:
                q = fa - fb
            else:
                q = fb - fa
                p = -p
            a = b
            fa = fb
            if p <= (m - b)*q:
                b = b + p/q
                fb = f(b)
            else:            
                b = m
                fb = f(b)

        return b

    
class Option(object):

    def __init__(self, V_mkt, X, K, tau, r, OptionType, 
                 ModelType):

        self.V_mkt = V_mkt # option market price
        self.X = X # underlying spot 
        self.K = K # strike
        self.tau = tau / 365.0 # time to maturity (yearly units, ACT/365)
        self.r = r # risk-free rate
        
        self.__OptionType = OptionType # either "Call" or "Put"
        self.__ModelType = ModelType # either "BlackScholes" or "Bachelier"
        
        self.__PutCallParityOffset = None # price offset w.r.t. call price 
        
    def getOptionType(self):
        return self.__OptionType

    def getModelType(self):
        return self.__ModelType
    
    def getPutCallParityOffset(self):
        return self.__PutCallParityOffset

    def setPutCallParityOffset(self, value):
        self.__PutCallParityOffset = value
    
    # Call - BS
    def callOptionPriceBlackScholes(self):
        raise NameError("Abstract Black-Scholes Call Option Price Calculator")

    # Put - BS
    def putOptionPriceBlackScholes(self):
        raise NameError("Abstract Black-Scholes Put Option Price Calculator")

    # Call - Bachelier
    def callOptionPriceBachelier(self):
        raise NameError("Abstract Bachelier Call Option Price Calculator")

    # Put - Bachelier
    def putOptionPriceBachelier(self):
        raise NameError("Abstract Bachelier Put Option Price Calculator")

    def getOptionPrice(self):
        """
        Returns a callable method to price call/put options under BS/Bac models.
        """
        
        if self.getModelType() == "BlackScholes": 
            
            if self.getOptionType() == "Call":
                return self.callOptionPriceBlackScholes
            
            elif self.getOptionType() == "Put":
                return self.putOptionPriceBlackScholes
        
            else:          
                raise NameError("Option Type not recognized")

        elif self.getModelType() == "Bachelier":

            if self.getOptionType() == "Call":
                return self.callOptionPriceBachelier
            
            elif self.getOptionType() == "Put":
                return self.putOptionPriceBachelier

            else:          
                raise NameError("Option Type not recognized")
            
        else:
            raise NameError("Model Type not supported")
        
    def impliedVol(self, rootFind):
        """
        Returns the implied volatility. Needs in input an instance "rootFind" of the
        RootFinder class.
        """
        
        # distance between model and market
        modelMisPrice = lambda x, self=self: self.getOptionPrice()(x) - self.V_mkt
        
        return rootFind.getRootFindMethod()(modelMisPrice)
    
def getProduct(product = "Stock", *args):
    """
    Factory method to choose the appropriate child class of Option.
    """
    
    products = {"Stock": Stock(*args),
                "Future": Future(*args)}
    
    return products[product]
        
class Stock(Option):

    def __init__(self, V_mkt, X, K, tau, r, OptionType, ModelType):
        
        super().__init__(V_mkt, X, K, tau, r, OptionType, ModelType)
        
        self.setPutCallParityOffset(K * np.exp(-r * tau) - X)      
    
    # Call - BS
    def callOptionPriceBlackScholes(self, sigma):
        """
        Black-Scholes European Call Option Price on Stock as a function of BS implied volatility.

        Comments: this is the plain Black-Scholes formula.
        """
            
        d1 = (np.log(self.X / self.K) + (self.r + 0.5 * sigma**2.0) * self.tau) / (sigma * np.sqrt(self.tau))
        d2 = d1 - sigma * np.sqrt(self.tau)
        
        V_call = self.X * norm.cdf(d1) - np.exp(-self.r * self.tau) * self.K * norm.cdf(d2)
        
        return V_call


    # Put - BS
    def putOptionPriceBlackScholes(self, sigma):
        """
        Black-Scholes European Put Option Price on Stock as a function of BS implied volatility.
        
        Comments: derived from the result for the call option and put-call parity.
        """
        
        return self.callOptionPriceBlackScholes(sigma) + self.getPutCallParityOffset()
        
    # Call - Bachelier
    def callOptionPriceBachelier(self, sigma):
        """
        Bachelier European Call Option Price on Stock as a function of normal implied volatility.
        
        Comments: I'm not very confident with normal volatility quoting for options on stocks.
                  This implementation follows section 3.3 of Musiela-Rutkowski 
                  "Martingale Methods in Financial Modelling" (2nd ed.), which basically 
                  assumes dS = (rS)dt + (sigma)dW under Q. Also re-derived at:
                  https://quant.stackexchange.com/questions/32863/bachelier-model-call-option-pricing-formula
        """
        
        K_star = self.K * np.exp(-self.r * self.tau) # discounted strike
        v_tT = 0.5 * (sigma**2 / self.r) * (1.0 - np.exp(-2.0 * self.r * self.tau)) # integrated volatility
        
        d = (self.X - K_star) / v_tT
    
        V_call = (self.X - K_star) * norm.cdf(d) + v_tT * norm.pdf(d)
        
        return V_call

    # Put - Bachelier
    def putOptionPriceBachelier(self, sigma):
        """
        Bachelier European Put Option Price on Stock as a function of normal implied volatility.

        Comments: derived from the result for the call option and put-call parity.
        """
        
        V_call = self.callOptionPriceBachelier(sigma)
        
        V_put = V_call + self.getPutCallParityOffset()
        
        return V_put

            
class Future(Option):
    
    def __init__(self, V_mkt, X, K, tau, r, OptionType, ModelType):
        
        super().__init__(V_mkt, X, K, tau, r, OptionType, ModelType)
        
        self.setPutCallParityOffset((K - X) * np.exp(-r * tau))
    
    # Call - BS
    def callOptionPriceBlackScholes(self, sigma):
        """
        Black-Scholes European Call Option Price on Future as a function of BS implied volatility.
        
        Comments: this is the so-called Black-76 formula.
        """
 
        d1 = (np.log(self.X / self.K) + 0.5 * sigma**2.0 * self.tau) / (sigma * np.sqrt(self.tau))
        d2 = d1 - sigma * np.sqrt(self.tau)
        
        V_call = np.exp(-self.r * self.tau) * (self.X * norm.cdf(d1) -  self.K * norm.cdf(d2))
        
        return V_call
    
    # Put - BS
    def putOptionPriceBlackScholes(self, sigma):
        """
        Black-Scholes European Put Option Price on Future as a function of BS implied volatility.

        Comments: derived from the result for the call option and put-call parity.
        """
        
        V_call = self.callOptionPriceBlackScholes(sigma)
        
        V_put = V_call + self.getPutCallParityOffset()
        
        return V_put
        
    # Call - Bachelier
    def callOptionPriceBachelier(self, sigma):
        """
        Bachelier European Call Option Price on Future as a function of normal implied volatility.
        
        Comments: this implements formula (A.54a) of SABR model paper http://web.math.ku.dk/~rolf/SABR.pdf
                  and should be the standard for futures options normal volatility quoting.
                  Here, it is assumed that the future price follows a normal martingale: dF = (sigma) dW (A.53a)
        """
        
        d = (self.X - self.K) / (sigma * np.sqrt(self.tau))
    
        V_call = (self.X - self.K) * norm.cdf(d) + sigma * np.sqrt(self.tau) * norm.pdf(d)
        
        return V_call

    # Put - Bachelier
    def putOptionPriceBachelier(self, sigma):
        """
        Bachelier European Put Option Price on Future as a function of normal implied volatility.

        Comments: derived from the result for the call option and put-call parity.
        """
        
        return self.callOptionPriceBachelier(sigma) + self.getPutCallParityOffset()

if __name__ == "__main__":
    
    import pandas as pd
    
    df = pd.read_csv("./input.csv")
    
    df["Implied Volatility"] = np.nan
    
    rootFind = RootFinder()
    rootFind.setRootFindMethod() # by default the root finder will be Dekker's method
    
    for rowNum, row in df.iterrows():
        
        underlyingType = df.loc[rowNum]["Underlying Type"]
        V_mkt          = df.loc[rowNum]["Market Price"]
        X              = df.loc[rowNum]["Underlying"]
        K              = df.loc[rowNum]["Strike"]
        tau            = df.loc[rowNum]["Days To Expiry"]
        r              = df.loc[rowNum]["Risk-Free Rate"]
        OptionType     = df.loc[rowNum]["Option Type"]
        ModelType      = df.loc[rowNum]["Model Type"]
        
        productSpecificOption = getProduct(underlyingType, V_mkt, X, K, tau, r, 
                                           OptionType, ModelType)
        
        calculatedImpliedVol = productSpecificOption.impliedVol(rootFind)
        
        df.at[rowNum, "Implied Volatility"] = calculatedImpliedVol
    
    df["Years To Expiry"] = df["Days To Expiry"]/365.0
    
    output = df.filter(["ID", "Underlying", "Strike", "Risk-Free Rate", 
                        "Years To Expiry", "Option Type", "Model Type", 
                        "Implied Volatility", "Market Price"], axis=1)
    
    output.rename(columns={"Underlying": "Spot"}, inplace=True)

    output.to_csv("./output.csv", index=False, na_rep="NA")    
        
        
        
