import secrets
from itertools import product as nest
from pathlib import Path
from random import shuffle
from re import search, sub
from time import ctime, sleep, time

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from progress.bar import IncrementalBar
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.expected_conditions import \
    element_to_be_clickable as beClickable
from selenium.webdriver.support.expected_conditions import \
    presence_of_element_located as presence
from selenium.webdriver.support.ui import WebDriverWait as waiter

# Set up the Google Drive API
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Gets the spreadsheet's data
allData = client.open_by_key(secrets.sheet)
listSheet = allData.sheet1
profileList = listSheet.col_values(1); profileList.pop(0); profileList = list(set(profileList))
# for i in range(len(profileList)): profileList[i] = "@" + profileList[i].replace(" ","").replace("@","").lower()
for i in range(len(profileList)): profileList[i] = profileList[i].replace(" ","").replace("@","").lower()

Path("./screenshots").mkdir(parents=True, exist_ok=True)

# RAFFLE CLASS
class raffle:
    def __init__(self, link: str, profilesPerComment: int, allowStores=False, allowRepeating=False):
        self.link = "https://www.instagram.com/p/" + \
            sub("(https://){0,1}(www\.){0,1}(instagram\.com/p/){0,1}",
                "", link).replace("/", "").replace(" ", "")

        self.profilesPerComment = profilesPerComment
        self.allowStores = allowStores
        self.allowRepeating = allowRepeating

# BOT CLASS
class instaBot:
    def __init__(self, username: str, password: str, invisible=True, displayConsoleLog=True):
        self.username = username.lower().replace(" ", "").replace("@", "")
        self.password = password.replace(" ", "")
        self.displayConsoleLog = displayConsoleLog

        self.openBrowser(invisible)

        try:
            self.login()

            self.follow("vvianalucas")

        except: self.closeBrowser()

    # 0PENS BROWSER
    def openBrowser(self, invisible=True):
        if not self.displayConsoleLog:
            invisible = False

        if invisible:
            opt = Options()
            opt.add_argument('--headless')

            browser = webdriver.Firefox(options=opt)
            if self.displayConsoleLog:
                print(
                    f"\n{'@' + self.username} ::: Invisible browser opened successfully.\n")

        else:
            browser = webdriver.Firefox()
            if self.displayConsoleLog:
                print(
                    f"\n{'@' + self.username} ::: Visible browser opened successfully.\n")

        self.driver = browser

    # LOGS IN TO ACCOUNT ON INSTAGRAM WEB
    def login(self):
        self.driver.get("https://instagram.com")  # Opens Instagram login page
        if self.displayConsoleLog:
            print(f"\n{'@' + self.username} ::: instagram.com successfully opened.")

        try:
            # Waits until the page is loaded enough to enter username
            usernameInput = waiter(self.driver, 20).until(
                presence((By.XPATH, "//input[@name=\"username\"]")))
            if self.displayConsoleLog:
                print(
                    f"{'@' + self.username} ::: Page finished loading successfully.")

            # Enters username
            usernameInput.send_keys(self.username)
            if self.displayConsoleLog:
                print(f"{'@' + self.username} ::: Username entered successfully.")

            # Enters password
            self.driver.find_element_by_xpath(
                "//input[@name=\"password\"]").send_keys(self.password)
            if self.displayConsoleLog:
                print(f"{'@' + self.username} ::: Password entered successfully.")

            # Clicks button to submit login info
            self.driver.find_element_by_xpath(
                '//button[@type="submit"]').click()
            if self.displayConsoleLog:
                print(f"{'@' + self.username} ::: Login submitted sucessfully.")

            waiter(self.driver,10, poll_frequency=0.1).until(
                presence(
                    (By.XPATH, "//button[contains(text(), 'Not Now')]")
                ) or 
                presence(
                    (By.XPATH,"//span[contains(text(), 'Instagram from Facebook')]")
                )
            )

        except:  # If the page takes longer than 10s to load, raises exception
            if self.displayConsoleLog:
                print(
                    f"{'@' + self.username} ::: Error while loading page (t > 10s).")

            # Saves screenshot
            screenshotName = "./screenshots/" + \
                ctime() + " ::: ERROR ::: LOGGING IN TO INSTAGRAM.png"
            self.driver.save_screenshot(screenshotName)
            if self.displayConsoleLog:
                print(
                    f"\n{'@' + self.username} ::: Screenshot saved: \"%s\".\n\n" % screenshotName)

            # Closes browser
            self.driver.quit()

            raise Exception("The page took too long to load.")

        return

    # SELECTS PROFILES FOR EACH COMMENT BASED ON NUMBER ALLOWED
    def selectComments(self, raf: raffle, profiles: list):
        self.profiles = profiles.copy() if raf.allowStores else removeStores(profiles, False)

        # Removes self from the list
        try:
            self.profiles.remove("@" + self.username)

        # If the list does not contain self
        except ValueError:
            if listSheet.col_values(1).count("@" + self.username) == 0:
                if self.displayConsoleLog:
                    print(f"\n{'@' + self.username} ::: The list doesn't contain self. Will include it in the spreadsheet.")

                listSheet.update("A" + str(firstEmptyCell(listSheet, "col", 1, True)), "@" + self.username)

                if self.displayConsoleLog:
                    print(f"{'@' + self.username} ::: Profile was successfully included in the sheet.")

        else:
            if self.displayConsoleLog:
                print(f"\n{'@' + self.username} ::: Removed self from the list.")

        # Follow every profile on the list if isn't followed already
        for prof in self.profiles:
            if not self.follow(prof):
                print(f"{'@' + self.username} ::: {'@' + prof} DOES NOT EXIST. Highly recommendable removing it from the spreadsheet.")
            

        # Number of profiles that won't be used
        remainder = len(self.profiles) % raf.profilesPerComment

        # Total number of comments that will be generated
        total = int(len(self.profiles)/raf.profilesPerComment)
        if self.displayConsoleLog:
            print(f"{'@' + self.username} ::: {total} comments will be generated and {remainder} profiles will remain unused.")

        # Shuffles the profile list
        shuffle(self.profiles)
        if self.displayConsoleLog:
            print(f"{'@' + self.username} ::: Profiles' list was shuffled successfully.")

        # List that will be populated with the ready-for-commenting self.profiles
        self.comments = []

        # List that will be populated with the unused profiles
        self.remaining = []

        tmp = 1  # Comment number
        for i in range(0, len(self.profiles), raf.profilesPerComment):

            # If self.comments isn't full yet
            if len(self.profiles) - i > remainder:
                # Empties the 'element' auxiliar variable
                element = ""

                # Puts together the required number of profiles for each comment
                for j in range(i, i+raf.profilesPerComment):
                    element += self.profiles[j] + " "

                # If the comment end in a whitespace, remove it
                element = sub("\s+$", "", element)

                # Saves the comments to the 'self.comments' list
                self.comments.append(element)

                if self.displayConsoleLog:
                    print(f"{'@' + self.username} ::: Comment {tmp}/{total} was successfully saved: {element}.")

                tmp += 1

            # If self.comments is full
            else:
                if self.displayConsoleLog:
                    print(f"{'@' + self.username} ::: All comments were saved successfully.")

                for k in range(remainder):
                    # Stores the remaining profiles
                    self.remaining.append(self.profiles[k+i])

                    if self.displayConsoleLog:
                        print(f"{'@' + self.username} ::: Remaining profile {k+1}/{remainder}: {self.profiles[k+i]}.")

                break  # Breaks out of the for-loop

        return

    # FOLLOW PROFILE
    def follow(self, profile: str):
        profile = profile.replace(" ", "").replace("@", "").lower()

        self.driver.get("https://www.instagram.com/" + profile + "/")

        # Waits for the page to fully load
        waiter(self.driver, 5).until(
            presence(
                (By.XPATH, '//img[@alt="Instagram"]')
            )
        )

        # Checks if the profile exists
        try: self.driver.find_element_by_xpath(f"//h2[contains(text(),'{profile}')]")

        # If it does not, return False
        except:
            try: self.driver.find_element_by_xpath("//p[contains(text(),'The link you followed may be broken, or the page may have been removed. ')]")

            except: raise Exception()

            else:
                return False

        if self.displayConsoleLog:
            print(f"\n{'@' + self.username} ::: Follow @" + profile + ".")
            print(f"{'@' + self.username} ::: Profile opened successfully.")

        breakpoint()
        # Checks if already follows the profile
        try:
            self.driver.find_element_by_xpath(
                "//header//span[@aria-label=\"Following\"]"
            )

        # If it doesn't, an exception will be caught
        except:
            # Checks if already requested to follow
            try:
                self.driver.find_element_by_xpath(
                    "//header//button[contains(text(),'Requested')]"
                )

            # If it didn't:
            except:
                if self.displayConsoleLog:
                    print(f"{'@' + self.username} ::: The profile isn't followed yet.")

                # Clicks the follow button
                self.driver.find_element_by_xpath(
                    "//header//button[contains(text(),'Follow')]"
                ).click()

                if self.displayConsoleLog:
                    print(f"{'@' + self.username} ::: 'Follow' button clicked successfully.")
                
                # Checks if it is now following
                try:
                    waiter(self.driver, 3).until(
                        presence(
                            (By.XPATH, "//header//span[@aria-label=\"Following\"]")
                        )
                    )

                # If it isn't, an exception will be caught
                except:
                    # Confirms that a follow was requested (private profile)
                    waiter(self.driver, 4).until(beClickable(
                        (By.XPATH, "//header//button[contains(text(),'Requested')]")
                    ))
                    if self.displayConsoleLog:
                        print(f"{'@' + self.username} ::: Profile is private. A follow request was sent.")

            # If it was:
            else:
                if self.displayConsoleLog:
                    print(
                        f"{'@' + self.username} ::: Profile is private and a follow request was already sent.")

        else:
            if self.displayConsoleLog:
                print(
                    f"{'@' + self.username} ::: The profile is already being followed.")

        return True

    # COMMENTS PROFILES TO RAFFLE'S INSTAGRAM POST
    def commentRaffle(self, raf: raffle):
        # Opens the raffle's Intagram post
        self.driver.get(raf.link)

        # Waits for the page to fully load
        waiter(self.driver, 5).until(
            presence((By.XPATH, '//img[@alt="Instagram"]'))
        )

        # Raffles title (raffle's owner profile name)
        title = self.driver.title
        if " on Instagram: \"" in title: title = sub("\son\sInstagram:.+$", "",title)
        elif search("^Instagram\sphoto\sby\s", title): title = sub("^Instagram\sphoto\sby\s|•.+$","",title)

        if  self.displayConsoleLog:
            print(f"\n{'@' + self.username} ::: {title} ::: The raffle's post was successfully opened.")
 
        # Likes the post if it wasn't liked already
        picture = self.driver.find_element_by_xpath(f"//div[@class=\"eLAPa kPFhm\"]")
        ActionChains(self.driver).double_click(picture).perform() # Double clicks the picture

        print(f"\n{'@' + self.username} ::: {title} ::: The post was successfully liked.")

        # Follows the owner if it wasn't followed already
        followButton = self.driver.find_element_by_xpath("//button[contains(text(),'Follow')]")

        if followButton.text == "Follow":
            followButton.click()

            waiter(self.driver,5).until(
                presence(
                    (By.XPATH, "//button[contains(text(),'Following')]")
                )
            )

            if self.displayConsoleLog:
                print(f"\n{'@' + self.username} ::: {title} ::: The profile was followed successfully.")

        elif followButton.text == "Following":
            self.driver.find_element_by_xpath(
                "//button[contains(text(),'Following')]"
            )

            if self.displayConsoleLog:
                print(f"\n{'@' + self.username} ::: {title} ::: The profile was already followed.")

        total = len(self.comments)

        hasRefreshed = [False] * total

        i = 1
        for comment in self.comments:
            # Will keep trying to comment until successfull
            while(True):
                # breakpoint()
                try:
                    # Waits until the page is loaded enough to comment
                    waiter(self.driver, 10).until(
                        beClickable(
                            (By.XPATH, '//textarea[@placeholder="Add a comment…"]')
                        )
                    )

                    # If the page wasn't just refreshed for the last comment
                    if  self.displayConsoleLog and i > 1 and not hasRefreshed[i-1]:
                        print(
                            f"{'@' + self.username} ::: {title}  ::: Comment {i-1}/{total} posted successfully.")

                    # If the page was just refreshed for the last comment
                    if  self.displayConsoleLog and hasRefreshed[i-2]:
                        print(
                            f"{'@' + self.username} ::: {title}  ::: Timeout avoided successfully.")

                    # Activates the comment box
                    self.driver.find_element_by_xpath(
                        '//textarea[@placeholder="Add a comment…"]').click()

                    # Writes the comment
                    self.driver.find_element_by_xpath(
                        '//textarea[@placeholder="Add a comment…"]').send_keys(comment)
                    if  self.displayConsoleLog:
                        print(
                            f"{'@' + self.username} ::: {title}  ::: Comment {i}/{total} was successfully written.")

                    # Submits the comment
                    self.driver.find_element_by_xpath(
                        '//button[@type="submit"]').click()
                    if  self.displayConsoleLog:
                        print(
                            f"{'@' + self.username} ::: {title}  ::: Comment {i}/{total} was successfully submitted.")

                except:
                    if  self.displayConsoleLog:
                        print(
                            f"\n{'@' + self.username} ::: {title}  ::: Error in comment {i}/{total}.")

                    screenshotName = "./screenshots/" + \
                        ctime() + " ::: ERROR ::: COMMENTING ON RAFFLE.png"
                    self.driver.save_screenshot(screenshotName)

                    if  self.displayConsoleLog:
                        print(
                            f"\n{'@' + self.username} ::: {title}  ::: Screenshot saved: \"{screenshotName}\".\n\n")

                    self.driver.quit()

                    raise Exception("Error while commenting.")

                # Checks if the comment was successfully posted
                # of if it's on timeout
                try:
                    waiter(self.driver, 5, poll_frequency=0.1).until(
                        presence(
                            (By.XPATH, "//button[contains(text(),'Retry')]") or 
                            (By.XPATH, "//p[@class=\"gxNyb\" and contains(text(),'Couldn't post comment.')]") or
                            (By.XPATH, "//div[@class=\"CgFia \"]/div[@class=\"HGN2m XjicZ\"]")
                        )
                    )

                # If it was posted, break out of the while-loop
                except:
                    break

                # If it's on timeout:
                else:
                    # If the page wasnt refreshed yet for this comment:
                    if not hasRefreshed[i-1]:
                        # Sets the refresh status to True
                        hasRefreshed[i-1] = True

                        if  self.displayConsoleLog:
                            print(
                                f"{'@' + self.username} ::: {title}  ::: Timeout. Refreshing page to try and avoid it.")

                        # Refreshes page
                        try:
                            self.driver.refresh()

                        except:
                            if  self.displayConsoleLog:
                                print(
                                    f"\n{'@' + self.username} ::: {title}  ::: Error in comment {i}/{total}, while refreshing page.")

                            screenshotName = "./screenshots/" + \
                                ctime() + " ::: ERROR ::: COMMENTING ON RAFFLE.png"
                            self.driver.save_screenshot(screenshotName)

                            if  self.displayConsoleLog:
                                print(
                                    f"\n{'@' + self.username} ::: {title}  ::: Screenshot saved: \"{screenshotName}\".\n\n")

                            self.driver.quit()

                            raise Exception("Error while refreshing page.")

                        else:
                            if  self.displayConsoleLog:
                                print(
                                    f"{'@' + self.username} ::: {title}  ::: Page refreshed successfully.")

                    # If the page was already refreshed for this comment:
                    else:
                        timeout = True

                        while(timeout):
                            sleepingTime = 3  # in minutes

                            if  self.displayConsoleLog:
                                # Sleeps for 'sleepingTime' minutes, displaying progress bar
                                with IncrementalBar(f"{'@' + self.username} ::: {title}  ::: Timeout. Wait {sleepingTime}min.", max=60*sleepingTime, suffix='%(percent)d%%') as bar:
                                    for _ in range(60*sleepingTime):
                                        sleep(1)
                                        bar.next()

                            # Sleeps for 'sleepingTime' minutes
                            else: sleep(60*sleepingTime)


                            # Try and submit the comment again
                            waiter(self.driver, 2).until(
                                presence(
                                    (By.XPATH, '//button[@type="submit"]'))
                            ).click()

                            if  self.displayConsoleLog:
                                print(
                                    f"{'@' + self.username} ::: {title}  ::: Comment {i}/{total} submitted again.")

                            try:  # Checks if it's still in timeout
                                waiter(self.driver, 5, poll_frequency=0.1).until(
                                    presence(
                                        (By.XPATH, "//button[contains(text(),'Retry')]") or
                                        (By.XPATH, "//p[@class=\"gxNyb\" and contains(text(),'Couldn't post comment.')]") or
                                        (By.XPATH, "//div[@class=\"CgFia \"]/div[@class=\"HGN2m XjicZ\"]")
                                    )
                                )

                            except:  # If it's not
                                if  self.displayConsoleLog:
                                    print(
                                        f"{'@' + self.username} ::: {title}  ::: Timeout passed successfully.")

                                hasRefreshed[i-1] = False

                                timeout = False

                            else:
                                timeout = True

                        # If the comment was successfull, break out of the while-loop
                        break

            i += 1

        if  self.displayConsoleLog:
            print(
                f"{'@' + self.username} ::: {title}  ::: All comments were successfully posted.\n")

        return

    # QUITS BROWSER
    def closeBrowser(self):
        try:
            self.driver.quit()

            if self.displayConsoleLog:
                print(
                    f"\n{'@' + self.username} ::: The browser was successfully closed.\n")

        except:
            pass

        return

# RETURN THE COORDTYPE-COORDINATES TO THE FIRST EMPTY CELL AT THE END OF EITHER A COLUMN OR A ROW
def firstEmptyCell(worksheet: gspread.models.Worksheet, coordType: str, coord: int, header = True):
    if coordType != "col" and coordType != "row": Exception("This function's 'coordType' must be either 'col' or 'row'.")

    tmp = worksheet.col_values(coord) if coordType == "col" else worksheet.row_values(coord)
    if header: tmp.pop(0)
    result = len(tmp) + 2 if header else len(tmp) + 1

    return result

# REMOVES ITEMS THAT MATCH DENIED TEMPLATES FROM LIST
def removeStores(inputList: list, displayConsoleLog=True):
    denyTemplate = ["snkrs", "sneakers", "drop", "hype", "store",
                "grail", "sneaker", "streetwear", "stwr", "company", "apparel"]

    denylist = []  # List that will be populated with the store profiles
    newList = inputList.copy()  # List that will contain only non-store profiles

    # Adds all store profiles to 'denylist'
    for element, target in nest(newList, denyTemplate):
        if target in element:
            denylist.append(element)
            break

    if displayConsoleLog: print()

    # Removes all store profiles (denylist) from 'newList'
    for i in range(len(denylist)):
        element = denylist[i]
        newList.remove(element)

        if displayConsoleLog:
            print("REMOVING STORES ::: Profile %d/%d (%s) was successfully removed." 
                % (i+1, len(denylist), element))

    if displayConsoleLog: print()

    return newList


if __name__ == "__main__":
    testRaffle = raffle("CE-Z6u6h1rKps8pF-Wm-TN5-ctWHACycfOtaJ00", 4, False, False)

    try: 
        testBot = instaBot(secrets.login, secrets.pw, False)
    except: exit()

    try:
        testBot.selectComments(testRaffle, profileList)

        testBot.commentRaffle(testRaffle)

        testBot.closeBrowser()

    except: instaBot.closeBrowser()
