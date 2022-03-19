import pandas as pd
import seaborn as sns

sns.set_style('whitegrid')

import warnings
warnings.filterwarnings('ignore')
import pickle

from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler

dataframe_org = pd.read_csv('train.csv', delimiter='|')

#dataframe_org.drop(dataframe_org.loc[dataframe_org['trustLevel']>=3].index, inplace=True)

dataframe = dataframe_org.copy()

########### manual feature generation ##########

# totalScanned:
dataframe['totalScanned'] = dataframe['scannedLineItemsPerSecond'] * dataframe['totalScanTimeInSeconds']
# avgValuePerScan:
dataframe['avgTimePerScan'] = 1/ dataframe['scannedLineItemsPerSecond']
dataframe['avgValuePerScan'] = dataframe['avgTimePerScan'] * dataframe['valuePerSecond']
# manual feature generation - "totalScanned" ratios
# withoutRegisPerPosition
dataframe['withoutRegisPerPosition'] = dataframe['scansWithoutRegistration'] / dataframe['totalScanned']
# ratio of scansWithoutRegis in totalScan
# equivalent to lineItemVoidsPerPosition
# Might indicate how new or ambivalent a customer is. Expected to be higher for low "trustLevel"
# quantiModPerPosition
dataframe['quantiModPerPosition'] = dataframe['quantityModifications'] / dataframe['totalScanned']
# ratio of quanityMods in totalScan
# manual feature generation - "grandTotal" ratios
# lineItemVoidsPerTotal
dataframe['lineItemVoidsPerTotal'] = dataframe['lineItemVoids'] / dataframe['grandTotal']
# withoutRegisPerTotal
dataframe['withoutRegisPerTotal'] = dataframe['scansWithoutRegistration'] / dataframe['grandTotal']
# quantiModPerTotal
dataframe['quantiModPerTotal'] = dataframe['quantityModifications'] / dataframe['grandTotal']
# manual feature generation - "totalScanTimeInSeconds" ratios
# lineItemVoidsPerTime
dataframe['lineItemVoidsPerTime'] = dataframe['lineItemVoids'] / dataframe['totalScanTimeInSeconds']
# withoutRegisPerTime
dataframe['withoutRegisPerTime'] = dataframe['scansWithoutRegistration'] / dataframe['totalScanTimeInSeconds']
# quantiModPerTime
dataframe['quantiModPerTime'] = dataframe['quantityModifications'] / dataframe['totalScanTimeInSeconds']

########### end manual feature generation ###########

X_base=dataframe.drop('fraud',axis=1)
y_base=dataframe['fraud']

sc=StandardScaler()
X_base1=sc.fit_transform(X_base)

sv1=SVC(C=800, gamma=0.0009, kernel='rbf')
svc1=sv1.fit(X_base1,y_base)

pickle.dump(svc1,open('model1.pkl','wb'))
