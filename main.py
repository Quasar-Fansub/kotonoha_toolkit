from nicegui import ui,run,app
from tkinter import filedialog, Tk

import os
import sys
import shutil
import ctypes
import subprocess

import asyncio

import re
import json
import unicodedata
from io import StringIO
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import yt_dlp

import pylrc
import pysrt
from webvtt import WebVTT

import httpx
from bs4 import BeautifulSoup

from PyDeepLX import PyDeepLX
from openai import OpenAI

# 解决 HiDPI 问题
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# 输出错误日志
sys.stderr = open("error_log.txt","w",encoding="utf-8")

# 设置资源文件夹
if getattr(sys, 'frozen', False):
    static_folder = os.path.join(sys._MEIPASS, 'static')
    internal_dir = os.path.join(sys._MEIPASS, '_internal')
    # 设置 WebView2 的用户数据文件夹
    webview2_data_folder = os.path.join(internal_dir, 'WebView2')
    
    os.environ["WEBVIEW2_USER_DATA_FOLDER"] = webview2_data_folder
else:
    static_folder = 'static'

app.add_static_files('/static', static_folder)

# 配置加载函数
def load_settings():
    global accept_gplv3,save_path, video_directory_name, cookies_file, description_template, tags_mapping
    global lyrics_directory_name, gpt_character_prompt, gpt_api_base,gpt_key
    global gpt_model_list, gpt_model_names, selected_model, price

    if not os.path.exists('settings.json'):
        default_settings = {
            "accept_gplv3": False,
            "save_path": "D:\\Kotonoha Toolkit\\",
            "video": {
                "directory_name": "视频",
                "cookies_file": "cookies.txt",
                "description_template": "此视频转载自{platform}，链接见上\n\n原标题：{title}\n原作者：{author}\n原标签：{tags}\n投稿时间：{upload_date}\n原简介：\n{description}",
                "tags_mapping": {
                    "VOICEROID劇場": "VOICEROID剧场",
                    "ボイスロイド劇場​​​​": "VOICEROID剧场",
                    "ボイスロイド実況": "VOICEROID实况",
                    "ソフトウェアトーク劇場": "Software Talk剧场",
                    "琴葉茜": "琴叶茜",
                    "琴葉葵": "琴叶葵",
                    "琴葉姉妹": "琴叶姐妹",
                    "結月ゆかり": "结月缘",
                    "紲星あかり": "绁星灯",
                    "東北きりたん": "东北切蒲英",
                    "東北ずん子": "东北俊子",
                    "東北イタコ": "东北伊达子"
                }
            },
            "lyrics": {
                "directory_name": "歌词"
            },
            "translator": {
                "gpt_api_base": "https://api.openai.com/v1/",
                "gpt_api_key": False,
                "gpt_character_prompt":"琴葉葵=琴叶葵 琴葉茜=琴叶茜 結月ゆかり=结月缘\n紲星あかり=绁星灯 弦巻マキ=弦卷真纪\n東北ずん子=东北俊子 東北きりたん=东北切蒲英 東北イタコ=东北伊达子",
                "gpt_models": [
                    { "model": "gpt-4o", "price": 2.5 },
                    { "model": "gpt-3.5-turbo", "price": 0.3 }
                ]
            }
        }
        
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(default_settings, f, ensure_ascii=False, indent=4)
            ui.notify("没找到配置文件，帮你装好了默认配置文件啦~ (p≧w≦q)", position='top-right', type='positive')

    with open('settings.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    accept_gplv3 = data['accept_gplv3']
    save_path = data['save_path']

    video_directory_name = data['video']['directory_name']
    cookies_file = data['video']['cookies_file']
    description_template = data['video']['description_template']
    tags_mapping = data['video']['tags_mapping']
    lyrics_directory_name = data['lyrics']['directory_name']

    gpt_api_base = data['translator']['gpt_api_base']
    gpt_key = data['translator']['gpt_api_key']
    gpt_character_prompt = data['translator']['gpt_character_prompt']

    gpt_model_list = data["translator"]["gpt_models"]
    gpt_model_names = [model_info["model"] for model_info in gpt_model_list]

    selected_model = gpt_model_names[0] if gpt_model_names else ""
    price = next((model_info["price"] for model_info in gpt_model_list if model_info["model"] == selected_model), 0)

# 初始加载设置
load_settings()


# 一些必要的变量
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3861.400 QQBrowser/10.7.4313.400'}
client = OpenAI(
    base_url=gpt_api_base,
    api_key=gpt_key,
)

title_mapping = {
    "/": "／",
    "?": "？",
    "|": "｜",
    '"': "“",
    "#": "＃"
}

gpl_v3_text = """GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright © 2007 Free Software Foundation, Inc. <https://fsf.org/>

Everyone is permitted to copy and distribute verbatim copies of this license document, but changing it is not allowed.

Preamble
The GNU General Public License is a free, copyleft license for software and other kinds of works.

The licenses for most software and other practical works are designed to take away your freedom to share and change the works. By contrast, the GNU General Public License is intended to guarantee your freedom to share and change all versions of a program--to make sure it remains free software for all its users. We, the Free Software Foundation, use the GNU General Public License for most of our software; it applies also to any other work released this way by its authors. You can apply it to your programs, too.

When we speak of free software, we are referring to freedom, not price. Our General Public Licenses are designed to make sure that you have the freedom to distribute copies of free software (and charge for them if you wish), that you receive source code or can get it if you want it, that you can change the software or use pieces of it in new free programs, and that you know you can do these things.

To protect your rights, we need to prevent others from denying you these rights or asking you to surrender the rights. Therefore, you have certain responsibilities if you distribute copies of the software, or if you modify it: responsibilities to respect the freedom of others.

For example, if you distribute copies of such a program, whether gratis or for a fee, you must pass on to the recipients the same freedoms that you received. You must make sure that they, too, receive or can get the source code. And you must show them these terms so they know their rights.

Developers that use the GNU GPL protect your rights with two steps: (1) assert copyright on the software, and (2) offer you this License giving you legal permission to copy, distribute and/or modify it.

For the developers' and authors' protection, the GPL clearly explains that there is no warranty for this free software. For both users' and authors' sake, the GPL requires that modified versions be marked as changed, so that their problems will not be attributed erroneously to authors of previous versions.

Some devices are designed to deny users access to install or run modified versions of the software inside them, although the manufacturer can do so. This is fundamentally incompatible with the aim of protecting users' freedom to change the software. The systematic pattern of such abuse occurs in the area of products for individuals to use, which is precisely where it is most unacceptable. Therefore, we have designed this version of the GPL to prohibit the practice for those products. If such problems arise substantially in other domains, we stand ready to extend this provision to those domains in future versions of the GPL, as needed to protect the freedom of users.

Finally, every program is threatened constantly by software patents. States should not allow patents to restrict development and use of software on general-purpose computers, but in those that do, we wish to avoid the special danger that patents applied to a free program could make it effectively proprietary. To prevent this, the GPL assures that patents cannot be used to render the program non-free.

The precise terms and conditions for copying, distribution and modification follow.

TERMS AND CONDITIONS
0. Definitions.
“This License” refers to version 3 of the GNU General Public License.

“Copyright” also means copyright-like laws that apply to other kinds of works, such as semiconductor masks.

“The Program” refers to any copyrightable work licensed under this License. Each licensee is addressed as “you”. “Licensees” and “recipients” may be individuals or organizations.

To “modify” a work means to copy from or adapt all or part of the work in a fashion requiring copyright permission, other than the making of an exact copy. The resulting work is called a “modified version” of the earlier work or a work “based on” the earlier work.

A “covered work” means either the unmodified Program or a work based on the Program.

To “propagate” a work means to do anything with it that, without permission, would make you directly or secondarily liable for infringement under applicable copyright law, except executing it on a computer or modifying a private copy. Propagation includes copying, distribution (with or without modification), making available to the public, and in some countries other activities as well.

To “convey” a work means any kind of propagation that enables other parties to make or receive copies. Mere interaction with a user through a computer network, with no transfer of a copy, is not conveying.

An interactive user interface displays “Appropriate Legal Notices” to the extent that it includes a convenient and prominently visible feature that (1) displays an appropriate copyright notice, and (2) tells the user that there is no warranty for the work (except to the extent that warranties are provided), that licensees may convey the work under this License, and how to view a copy of this License. If the interface presents a list of user commands or options, such as a menu, a prominent item in the list meets this criterion.

1. Source Code.
The “source code” for a work means the preferred form of the work for making modifications to it. “Object code” means any non-source form of a work.

A “Standard Interface” means an interface that either is an official standard defined by a recognized standards body, or, in the case of interfaces specified for a particular programming language, one that is widely used among developers working in that language.

The “System Libraries” of an executable work include anything, other than the work as a whole, that (a) is included in the normal form of packaging a Major Component, but which is not part of that Major Component, and (b) serves only to enable use of the work with that Major Component, or to implement a Standard Interface for which an implementation is available to the public in source code form. A “Major Component”, in this context, means a major essential component (kernel, window system, and so on) of the specific operating system (if any) on which the executable work runs, or a compiler used to produce the work, or an object code interpreter used to run it.

The “Corresponding Source” for a work in object code form means all the source code needed to generate, install, and (for an executable work) run the object code and to modify the work, including scripts to control those activities. However, it does not include the work's System Libraries, or general-purpose tools or generally available free programs which are used unmodified in performing those activities but which are not part of the work. For example, Corresponding Source includes interface definition files associated with source files for the work, and the source code for shared libraries and dynamically linked subprograms that the work is specifically designed to require, such as by intimate data communication or control flow between those subprograms and other parts of the work.

The Corresponding Source need not include anything that users can regenerate automatically from other parts of the Corresponding Source.

The Corresponding Source for a work in source code form is that same work.

2. Basic Permissions.
All rights granted under this License are granted for the term of copyright on the Program, and are irrevocable provided the stated conditions are met. This License explicitly affirms your unlimited permission to run the unmodified Program. The output from running a covered work is covered by this License only if the output, given its content, constitutes a covered work. This License acknowledges your rights of fair use or other equivalent, as provided by copyright law.

You may make, run and propagate covered works that you do not convey, without conditions so long as your license otherwise remains in force. You may convey covered works to others for the sole purpose of having them make modifications exclusively for you, or provide you with facilities for running those works, provided that you comply with the terms of this License in conveying all material for which you do not control copyright. Those thus making or running the covered works for you must do so exclusively on your behalf, under your direction and control, on terms that prohibit them from making any copies of your copyrighted material outside their relationship with you.

Conveying under any other circumstances is permitted solely under the conditions stated below. Sublicensing is not allowed; section 10 makes it unnecessary.

3. Protecting Users' Legal Rights From Anti-Circumvention Law.
No covered work shall be deemed part of an effective technological measure under any applicable law fulfilling obligations under article 11 of the WIPO copyright treaty adopted on 20 December 1996, or similar laws prohibiting or restricting circumvention of such measures.

When you convey a covered work, you waive any legal power to forbid circumvention of technological measures to the extent such circumvention is effected by exercising rights under this License with respect to the covered work, and you disclaim any intention to limit operation or modification of the work as a means of enforcing, against the work's users, your or third parties' legal rights to forbid circumvention of technological measures.

4. Conveying Verbatim Copies.
You may convey verbatim copies of the Program's source code as you receive it, in any medium, provided that you conspicuously and appropriately publish on each copy an appropriate copyright notice; keep intact all notices stating that this License and any non-permissive terms added in accord with section 7 apply to the code; keep intact all notices of the absence of any warranty; and give all recipients a copy of this License along with the Program.

You may charge any price or no price for each copy that you convey, and you may offer support or warranty protection for a fee.

5. Conveying Modified Source Versions.
You may convey a work based on the Program, or the modifications to produce it from the Program, in the form of source code under the terms of section 4, provided that you also meet all of these conditions:

a) The work must carry prominent notices stating that you modified it, and giving a relevant date.
b) The work must carry prominent notices stating that it is released under this License and any conditions added under section 7. This requirement modifies the requirement in section 4 to “keep intact all notices”.
c) You must license the entire work, as a whole, under this License to anyone who comes into possession of a copy. This License will therefore apply, along with any applicable section 7 additional terms, to the whole of the work, and all its parts, regardless of how they are packaged. This License gives no permission to license the work in any other way, but it does not invalidate such permission if you have separately received it.
d) If the work has interactive user interfaces, each must display Appropriate Legal Notices; however, if the Program has interactive interfaces that do not display Appropriate Legal Notices, your work need not make them do so.
A compilation of a covered work with other separate and independent works, which are not by their nature extensions of the covered work, and which are not combined with it such as to form a larger program, in or on a volume of a storage or distribution medium, is called an “aggregate” if the compilation and its resulting copyright are not used to limit the access or legal rights of the compilation's users beyond what the individual works permit. Inclusion of a covered work in an aggregate does not cause this License to apply to the other parts of the aggregate.

6. Conveying Non-Source Forms.
You may convey a covered work in object code form under the terms of sections 4 and 5, provided that you also convey the machine-readable Corresponding Source under the terms of this License, in one of these ways:

a) Convey the object code in, or embodied in, a physical product (including a physical distribution medium), accompanied by the Corresponding Source fixed on a durable physical medium customarily used for software interchange.
b) Convey the object code in, or embodied in, a physical product (including a physical distribution medium), accompanied by a written offer, valid for at least three years and valid for as long as you offer spare parts or customer support for that product model, to give anyone who possesses the object code either (1) a copy of the Corresponding Source for all the software in the product that is covered by this License, on a durable physical medium customarily used for software interchange, for a price no more than your reasonable cost of physically performing this conveying of source, or (2) access to copy the Corresponding Source from a network server at no charge.
c) Convey individual copies of the object code with a copy of the written offer to provide the Corresponding Source. This alternative is allowed only occasionally and noncommercially, and only if you received the object code with such an offer, in accord with subsection 6b.
d) Convey the object code by offering access from a designated place (gratis or for a charge), and offer equivalent access to the Corresponding Source in the same way through the same place at no further charge. You need not require recipients to copy the Corresponding Source along with the object code. If the place to copy the object code is a network server, the Corresponding Source may be on a different server (operated by you or a third party) that supports equivalent copying facilities, provided you maintain clear directions next to the object code saying where to find the Corresponding Source. Regardless of what server hosts the Corresponding Source, you remain obligated to ensure that it is available for as long as needed to satisfy these requirements.
e) Convey the object code using peer-to-peer transmission, provided you inform other peers where the object code and Corresponding Source of the work are being offered to the general public at no charge under subsection 6d.
A separable portion of the object code, whose source code is excluded from the Corresponding Source as a System Library, need not be included in conveying the object code work.

A “User Product” is either (1) a “consumer product”, which means any tangible personal property which is normally used for personal, family, or household purposes, or (2) anything designed or sold for incorporation into a dwelling. In determining whether a product is a consumer product, doubtful cases shall be resolved in favor of coverage. For a particular product received by a particular user, “normally used” refers to a typical or common use of that class of product, regardless of the status of the particular user or of the way in which the particular user actually uses, or expects or is expected to use, the product. A product is a consumer product regardless of whether the product has substantial commercial, industrial or non-consumer uses, unless such uses represent the only significant mode of use of the product.

“Installation Information” for a User Product means any methods, procedures, authorization keys, or other information required to install and execute modified versions of a covered work in that User Product from a modified version of its Corresponding Source. The information must suffice to ensure that the continued functioning of the modified object code is in no case prevented or interfered with solely because modification has been made.

If you convey an object code work under this section in, or with, or specifically for use in, a User Product, and the conveying occurs as part of a transaction in which the right of possession and use of the User Product is transferred to the recipient in perpetuity or for a fixed term (regardless of how the transaction is characterized), the Corresponding Source conveyed under this section must be accompanied by the Installation Information. But this requirement does not apply if neither you nor any third party retains the ability to install modified object code on the User Product (for example, the work has been installed in ROM).

The requirement to provide Installation Information does not include a requirement to continue to provide support service, warranty, or updates for a work that has been modified or installed by the recipient, or for the User Product in which it has been modified or installed. Access to a network may be denied when the modification itself materially and adversely affects the operation of the network or violates the rules and protocols for communication across the network.

Corresponding Source conveyed, and Installation Information provided, in accord with this section must be in a format that is publicly documented (and with an implementation available to the public in source code form), and must require no special password or key for unpacking, reading or copying.

7. Additional Terms.
“Additional permissions” are terms that supplement the terms of this License by making exceptions from one or more of its conditions. Additional permissions that are applicable to the entire Program shall be treated as though they were included in this License, to the extent that they are valid under applicable law. If additional permissions apply only to part of the Program, that part may be used separately under those permissions, but the entire Program remains governed by this License without regard to the additional permissions.

When you convey a copy of a covered work, you may at your option remove any additional permissions from that copy, or from any part of it. (Additional permissions may be written to require their own removal in certain cases when you modify the work.) You may place additional permissions on material, added by you to a covered work, for which you have or can give appropriate copyright permission.

Notwithstanding any other provision of this License, for material you add to a covered work, you may (if authorized by the copyright holders of that material) supplement the terms of this License with terms:

a) Disclaiming warranty or limiting liability differently from the terms of sections 15 and 16 of this License; or
b) Requiring preservation of specified reasonable legal notices or author attributions in that material or in the Appropriate Legal Notices displayed by works containing it; or
c) Prohibiting misrepresentation of the origin of that material, or requiring that modified versions of such material be marked in reasonable ways as different from the original version; or
d) Limiting the use for publicity purposes of names of licensors or authors of the material; or
e) Declining to grant rights under trademark law for use of some trade names, trademarks, or service marks; or
f) Requiring indemnification of licensors and authors of that material by anyone who conveys the material (or modified versions of it) with contractual assumptions of liability to the recipient, for any liability that these contractual assumptions directly impose on those licensors and authors.
All other non-permissive additional terms are considered “further restrictions” within the meaning of section 10. If the Program as you received it, or any part of it, contains a notice stating that it is governed by this License along with a term that is a further restriction, you may remove that term. If a license document contains a further restriction but permits relicensing or conveying under this License, you may add to a covered work material governed by the terms of that license document, provided that the further restriction does not survive such relicensing or conveying.

If you add terms to a covered work in accord with this section, you must place, in the relevant source files, a statement of the additional terms that apply to those files, or a notice indicating where to find the applicable terms.

Additional terms, permissive or non-permissive, may be stated in the form of a separately written license, or stated as exceptions; the above requirements apply either way.

8. Termination.
You may not propagate or modify a covered work except as expressly provided under this License. Any attempt otherwise to propagate or modify it is void, and will automatically terminate your rights under this License (including any patent licenses granted under the third paragraph of section 11).

However, if you cease all violation of this License, then your license from a particular copyright holder is reinstated (a) provisionally, unless and until the copyright holder explicitly and finally terminates your license, and (b) permanently, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation.

Moreover, your license from a particular copyright holder is reinstated permanently if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of this License (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice.

Termination of your rights under this section does not terminate the licenses of parties who have received copies or rights from you under this License. If your rights have been terminated and not permanently reinstated, you do not qualify to receive new licenses for the same material under section 10.

9. Acceptance Not Required for Having Copies.
You are not required to accept this License in order to receive or run a copy of the Program. Ancillary propagation of a covered work occurring solely as a consequence of using peer-to-peer transmission to receive a copy likewise does not require acceptance. However, nothing other than this License grants you permission to propagate or modify any covered work. These actions infringe copyright if you do not accept this License. Therefore, by modifying or propagating a covered work, you indicate your acceptance of this License to do so.

10. Automatic Licensing of Downstream Recipients.
Each time you convey a covered work, the recipient automatically receives a license from the original licensors, to run, modify and propagate that work, subject to this License. You are not responsible for enforcing compliance by third parties with this License.

An “entity transaction” is a transaction transferring control of an organization, or substantially all assets of one, or subdividing an organization, or merging organizations. If propagation of a covered work results from an entity transaction, each party to that transaction who receives a copy of the work also receives whatever licenses to the work the party's predecessor in interest had or could give under the previous paragraph, plus a right to possession of the Corresponding Source of the work from the predecessor in interest, if the predecessor has it or can get it with reasonable efforts.

You may not impose any further restrictions on the exercise of the rights granted or affirmed under this License. For example, you may not impose a license fee, royalty, or other charge for exercise of rights granted under this License, and you may not initiate litigation (including a cross-claim or counterclaim in a lawsuit) alleging that any patent claim is infringed by making, using, selling, offering for sale, or importing the Program or any portion of it.

11. Patents.
A “contributor” is a copyright holder who authorizes use under this License of the Program or a work on which the Program is based. The work thus licensed is called the contributor's “contributor version”.

A contributor's “essential patent claims” are all patent claims owned or controlled by the contributor, whether already acquired or hereafter acquired, that would be infringed by some manner, permitted by this License, of making, using, or selling its contributor version, but do not include claims that would be infringed only as a consequence of further modification of the contributor version. For purposes of this definition, “control” includes the right to grant patent sublicenses in a manner consistent with the requirements of this License.

Each contributor grants you a non-exclusive, worldwide, royalty-free patent license under the contributor's essential patent claims, to make, use, sell, offer for sale, import and otherwise run, modify and propagate the contents of its contributor version.

In the following three paragraphs, a “patent license” is any express agreement or commitment, however denominated, not to enforce a patent (such as an express permission to practice a patent or covenant not to sue for patent infringement). To “grant” such a patent license to a party means to make such an agreement or commitment not to enforce a patent against the party.

If you convey a covered work, knowingly relying on a patent license, and the Corresponding Source of the work is not available for anyone to copy, free of charge and under the terms of this License, through a publicly available network server or other readily accessible means, then you must either (1) cause the Corresponding Source to be so available, or (2) arrange to deprive yourself of the benefit of the patent license for this particular work, or (3) arrange, in a manner consistent with the requirements of this License, to extend the patent license to downstream recipients. “Knowingly relying” means you have actual knowledge that, but for the patent license, your conveying the covered work in a country, or your recipient's use of the covered work in a country, would infringe one or more identifiable patents in that country that you have reason to believe are valid.

If, pursuant to or in connection with a single transaction or arrangement, you convey, or propagate by procuring conveyance of, a covered work, and grant a patent license to some of the parties receiving the covered work authorizing them to use, propagate, modify or convey a specific copy of the covered work, then the patent license you grant is automatically extended to all recipients of the covered work and works based on it.

A patent license is “discriminatory” if it does not include within the scope of its coverage, prohibits the exercise of, or is conditioned on the non-exercise of one or more of the rights that are specifically granted under this License. You may not convey a covered work if you are a party to an arrangement with a third party that is in the business of distributing software, under which you make payment to the third party based on the extent of your activity of conveying the work, and under which the third party grants, to any of the parties who would receive the covered work from you, a discriminatory patent license (a) in connection with copies of the covered work conveyed by you (or copies made from those copies), or (b) primarily for and in connection with specific products or compilations that contain the covered work, unless you entered into that arrangement, or that patent license was granted, prior to 28 March 2007.

Nothing in this License shall be construed as excluding or limiting any implied license or other defenses to infringement that may otherwise be available to you under applicable patent law.

12. No Surrender of Others' Freedom.
If conditions are imposed on you (whether by court order, agreement or otherwise) that contradict the conditions of this License, they do not excuse you from the conditions of this License. If you cannot convey a covered work so as to satisfy simultaneously your obligations under this License and any other pertinent obligations, then as a consequence you may not convey it at all. For example, if you agree to terms that obligate you to collect a royalty for further conveying from those to whom you convey the Program, the only way you could satisfy both those terms and this License would be to refrain entirely from conveying the Program.

13. Use with the GNU Affero General Public License.
Notwithstanding any other provision of this License, you have permission to link or combine any covered work with a work licensed under version 3 of the GNU Affero General Public License into a single combined work, and to convey the resulting work. The terms of this License will continue to apply to the part which is the covered work, but the special requirements of the GNU Affero General Public License, section 13, concerning interaction through a network will apply to the combination as such.

14. Revised Versions of this License.
The Free Software Foundation may publish revised and/or new versions of the GNU General Public License from time to time. Such new versions will be similar in spirit to the present version, but may differ in detail to address new problems or concerns.

Each version is given a distinguishing version number. If the Program specifies that a certain numbered version of the GNU General Public License “or any later version” applies to it, you have the option of following the terms and conditions either of that numbered version or of any later version published by the Free Software Foundation. If the Program does not specify a version number of the GNU General Public License, you may choose any version ever published by the Free Software Foundation.

If the Program specifies that a proxy can decide which future versions of the GNU General Public License can be used, that proxy's public statement of acceptance of a version permanently authorizes you to choose that version for the Program.

Later license versions may give you additional or different permissions. However, no additional obligations are imposed on any author or copyright holder as a result of your choosing to follow a later version.

15. Disclaimer of Warranty.
THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW. EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM “AS IS” WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU. SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

16. Limitation of Liability.
IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS), EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.

17. Interpretation of Sections 15 and 16.
If the disclaimer of warranty and limitation of liability provided above cannot be given local legal effect according to their terms, reviewing courts shall apply local law that most closely approximates an absolute waiver of all civil liability in connection with the Program, unless a warranty or assumption of liability accompanies a copy of the Program in return for a fee.

END OF TERMS AND CONDITIONS

How to Apply These Terms to Your New Programs
If you develop a new program, and you want it to be of the greatest possible use to the public, the best way to achieve this is to make it free software which everyone can redistribute and change under these terms.

To do so, attach the following notices to the program. It is safest to attach them to the start of each source file to most effectively state the exclusion of warranty; and each file should have at least the “copyright” line and a pointer to where the full notice is found.

    <one line to give the program's name and a brief idea of what it does.>
    Copyright (C) <year>  <name of author>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
Also add information on how to contact you by electronic and paper mail.

If the program does terminal interaction, make it output a short notice like this when it starts in an interactive mode:

    <program>  Copyright (C) <year>  <name of author>
    This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.
    This is free software, and you are welcome to redistribute it
    under certain conditions; type `show c' for details.
The hypothetical commands `show w' and `show c' should show the appropriate parts of the General Public License. Of course, your program's commands might be different; for a GUI interface, you would use an “about box”.

You should also get your employer (if you work as a programmer) or school, if any, to sign a “copyright disclaimer” for the program, if necessary. For more information on this, and how to apply and follow the GNU GPL, see <https://www.gnu.org/licenses/>.

The GNU General Public License does not permit incorporating your program into proprietary programs. If your program is a subroutine library, you may consider it more useful to permit linking proprietary applications with the library. If this is what you want to do, use the GNU Lesser General Public License instead of this License. But first, please read <https://www.gnu.org/licenses/why-not-lgpl.html>."""


###### 公用 ######
# 判断是否为数字
def is_number(s):    
    try: 
        float(s)        
        return True    
    except ValueError:  
        pass  
    try:        
        unicodedata.numeric(s)       
        return True    
    except (TypeError, ValueError):        
        pass    
        return False

# 确定FFmpeg安装情况
def is_ffmpeg_installed():
    return shutil.which('ffmpeg') is not None

# 除去颜色文本
def strip_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

# 路径选择
def select_path(is_file=True, file_types=None):
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    if is_file:
        path = filedialog.askopenfilename(filetypes=file_types)
    else:
        path = filedialog.askdirectory()
    
    root.destroy()
    return path

async def handle_path_selection(result_element, is_file=True, file_types=None):
    path = await asyncio.to_thread(select_path, is_file, file_types)
    if path:
        result_element.set_value(path)

# 接受GPLv3协议
async def accept_gplv3_button():
    await run.io_bound(save_accept_gplv3)
    ui.notify('已接受GPLv3', position='top-right', type='positive')
    dialog_gplv3.close()

def save_accept_gplv3():
    new_settings = {
        'accept_gplv3': True,
        'save_path': save_path,
        'video': {
            'directory_name': video_directory_name,
            'cookies_file': cookies_file,
            'description_template': description_template,
            'tags_mapping': tags_mapping,
        },
        'lyrics': {
            'directory_name': lyrics_directory_name,
        },
        'translator': {
            'gpt_api_base': gpt_api_base,
            'gpt_api_key': gpt_key,
            'gpt_character_prompt':gpt_character_prompt,
            'gpt_models': gpt_model_list
        },
    }
    save_settings(new_settings)

###### 视频 ######
# 判断视频平台
def getVideoPlatform(url):
    if "youtube.com/watch" in url:
        return "YouTube"

    elif "youtube.com/shorts" in url:
        return "YouTube Shorts"
    
    elif "nicovideo.jp" in url:
        return "Niconico"

    else:
        return False

# 更新按钮状态
def updateButtonStatus(url):
    if getVideoPlatform(url):
        get_info_button.enable()
    else:
        get_info_button.disable()

# 日期格式化
def format_upload_date(upload_date_str):
    try:
        # 处理 yyyymmdd 格式
        if len(upload_date_str) == 8:
            year = upload_date_str[:4]
            month = upload_date_str[4:6]
            day = upload_date_str[6:8]
            formatted_date = f"{year}-{month}-{day}"
        
        else:

            date_formats = [
                '%Y%m%d',      # yyyymmdd
                '%Y-%m-%d',    # yyyy-mm-dd
                '%d/%m/%Y',    # dd/mm/yyyy
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(upload_date_str, fmt)
                    formatted_date = parsed_date.strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue
            else:
                return upload_date_str
        
        current_time = datetime.now().strftime('%H:%M:%S')
        
        return f"{formatted_date} {current_time}"
    
    except Exception as e:
        print(f"日期格式化错误: {e}")
        return upload_date_str



# 标签清理
def clean_tags(tags):
    cleaned_tags = []
    for tag in tags:
        # 去除标签中的 # 符号
        cleaned_tag = tag.replace('#', '').strip()
        if cleaned_tag:
            cleaned_tags.append(cleaned_tag)
    
    return cleaned_tags


# 获取信息
def get_video_info(url):
    # yt-dlp 配置
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': False,
        'no_color': True,
    }

    # 创建 yt-dlp 对象
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # 提取视频信息
        info_dict = ydl.extract_info(url, download=False)
        
        # 提取具体信息
        platform = info_dict.get('extractor', '未知平台')
        title = info_dict.get('title', '未知标题')
        thumbnail = info_dict.get('thumbnail', '无封面')
        uploader = info_dict.get('uploader', '未知作者')
        
        # 格式化上传日期
        upload_date_raw = info_dict.get('upload_date', '未知日期')
        upload_date = format_upload_date(upload_date_raw)
        
        description = info_dict.get('description', '无描述')
        
        # 处理并清理标签
        tags_raw = info_dict.get('tags', [])
        tags = clean_tags(tags_raw)
        tags_str = ','.join(tags) if tags else '无标签'

        # 返回信息字典
        return url,platform,title,thumbnail,uploader,upload_date,description,tags_str,matchTags(tags_str)
    
# 获取Niconico视频标签
def get_niconico_tags(url):
    html=httpx.get(url,headers=headers)
    soup = BeautifulSoup(html, 'html.parser')

    data = soup.find_all('script')[0].text.strip()
    data_json = json.loads(data)
    tags_text=data_json["keywords"]

    return tags_text,matchTags(tags_text)

# 标签匹配
def matchTags(text):
    for translated in tags_mapping.items():
        replaced_string = ""
        for word in text.split(','):
            translated = tags_mapping.get(word, None)
            if translated is not None:
                replaced_string += translated + "\n"
    return replaced_string

# 信息呈现
async def getInfomation(input_url):
    n = ui.notification(timeout=None,message="唔姆姆…正在获取信息 (～￣▽￣)～",position='top-right',spinner=True)
    info_card.set_visibility(False)
    platform=await run.io_bound(getVideoPlatform,input_url)
    global title_path,thumbnail_url,info_text
    if platform=="Niconico":
        url,platform_name,title_text,thumbnail_url,author_text,uploadDate_text,description_text,tags_text,matched_tags=await run.io_bound(get_video_info,input_url)
        platform_name="Niconico"
        tags_text,matched_tags=await run.io_bound(get_niconico_tags,input_url)
    elif platform=="YouTube" or platform=="YouTube Shorts":
        url,platform_name,title_text,thumbnail_url,author_text,uploadDate_text,description_text,tags_text,matched_tags=await run.io_bound(get_video_info,input_url)
        platform_name="Youtube"
    else:
        n.dismiss()
        ui.notify("这不是N站或油管的链接呀 o(≧口≦)o",position='top-right',type='negative')
    
    title_path=title_text
    for a, b in title_mapping.items():
        title_path = title_path.replace(a, b)  

    info_text='''原链接：
['''+url+''']('''+url+''')

---

建议标题：
【VOICEROID剧场】'''+title_text+'''【授权汉化】

---

匹配标签：
'''+matched_tags+'''

---

建议简介：
```
'''+description_template.format(
    url=url,
    platform=platform_name,
    title=title_text,
    author=author_text,
    tags=tags_text,
    upload_date=uploadDate_text,
    description=description_text
)+'''
```'''
    cover.set_source("./static/loading.gif")
    cover.set_source(thumbnail_url)
    info.set_content(info_text)
    n.dismiss()
    info_card.set_visibility(True)

# 保存信息和封面按钮
async def saveCover(title_path, thumbnail_url):
    full_video_path = os.path.join(save_path, video_directory_name, title_path)
    if not os.path.exists(full_video_path):
        os.makedirs(full_video_path)
    
    info_file_path = os.path.join(full_video_path, '视频信息.txt')
    with open(info_file_path, 'w', encoding='utf-8') as f:
        f.write(info_text)
        ui.notify("呐呐！视频信息已保存为：" + info_file_path + " ( •̀ ω •́ )✧", position='top-right', type='positive')
    
    status, status_info = await run.io_bound(downloadCover, thumbnail_url, title_path)
    if status:
        ui.notify(status_info, position='top-right', type='positive')
    else:
        ui.notify(status_info, position='top-right', type='negative')

# 封面下载
def downloadCover(url, title):
    response = httpx.get(url)
    if response.status_code == 200:
        image_content = response.content
        cover_path = os.path.join(save_path, video_directory_name, title, "封面.jpg")
        with open(cover_path, "wb") as f:
            f.write(image_content)
        return True, f"封面放这里了哦，记得看看！：{cover_path} (p≧w≦q)"
    else:
        return False, f"呜哇!失败了：{response.status_code} o(≧口≦)o"

# 视频下载按钮
async def downloadVideoButton(title,video_url):
    try:
        downloadButton.disable()
        await download_video(title, video_url)
    finally:
        downloadButton.enable()

# 视频下载
async def download_video(title, url):
    if not is_ffmpeg_installed():
        result = await ffmpeg_dialog
        if result == 'tutorial':
            ui.run_javascript('window.open("https://www.ffmpeg.org/", "_blank")')
        return

    n = ui.notification(message="在努力下载啦，等一等哦~ (o゜▽゜)o☆",position='top-right', timeout=None, spinner=True)
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            percent = strip_ansi(d.get('_percent_str', '0%')).strip()
            speed = strip_ansi(d.get('_speed_str', 'N/A'))
            eta = strip_ansi(d.get('_eta_str', 'N/A'))
            n.message = f"[{percent} / {speed}] {title} ETA: {eta}"

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'progress_hooks': [progress_hook],
        'merge_output_format': 'mp4',
        'outtmpl': os.path.join(save_path, video_directory_name, title, '视频.%(ext)s'),
    }

    # 检查 cookies.txt 是否存在
    if os.path.exists(cookies_file):
        ydl_opts['cookiefile'] = cookies_file
        ui.notify("竟然找到了Cookies！好耶！ (★ ω ★)",position='top-right',type='positive')

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [url])
        
        n.dismiss()
        full_path = os.path.join(save_path, video_directory_name, title, "视频.mp4")
        ui.notify(f"视频放在这里好了！：{full_path} o(〃＾▽＾〃)o", position='top-right', type='positive')
    except Exception as e:
        n.dismiss()
        ui.notify(f"下载失败: {str(e)}", position='top-right', type='negative')


###### 音乐 ######
# 判断音乐平台
def getMusicPlatform(url):
    if "youtube.com" in url:
        return "YouTube"

    elif "music.163.com" in url:
        return "Netease"

    else:
        return False

# 更新按钮状态
def updateMusicButtonStatus(url):
    if getMusicPlatform(url):
        get_lyrics_button.enable()
    else:
        get_lyrics_button.disable()

# 获取歌词按钮
async def getLyrics(input_url):
    info_card_music.set_visibility(False)
    platform=await run.io_bound(getMusicPlatform,input_url)
    
    if platform=="Netease":
        n = ui.notification(timeout=None,message="等一等哦！正在获取歌词~ (o゜▽゜)o☆",position='top-right',spinner=True)
        global music_name_text,original_lyrics_text,translated_lyrics_text
        music_name_text,original_lyrics_text,translated_lyrics_text=await run.io_bound(getLyricsFromNeteaseMusic,input_url)

        music_title.set_text(music_name_text)
        original_lyrics.set_content(f"<pre style='white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word;'>{original_lyrics_text}</pre>")
        translate_lyrics.set_content(f"<pre style='white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word;'>{translated_lyrics_text}</pre>")

        for a, b in title_mapping.items():
             music_name_text = music_name_text.replace(a, b)  

        n.dismiss()
        info_card_music.set_visibility(True)
    elif platform=="YouTube":
        await getLyricsFromYoutube(input_url)
    else:
        n.dismiss()
        ui.notify("这才不是网易云或油管的链接吧！ ヽ(*。>Д<)o゜",position='top-right',type='negative')

# 网易云音乐：音乐ID提取
def getNeteaseMusicID(url):
    id_index = url.find('id=')
    if id_index != -1:
        song_id = url[id_index + 3:]
        return song_id
    else:
        return None

# 网易云音乐：音乐歌词获取
def getLyricsFromNeteaseMusic(url):
    music_id = getNeteaseMusicID(url)
    json_obj=httpx.get('http://music.163.com/api/song/lyric?id=' + music_id+ '&lv=1&kv=1&tv=-1',headers=headers).text
    html=httpx.get("https://music.163.com/song?id="+ music_id,headers=headers)
    soup = BeautifulSoup(html, 'html.parser')
    data = soup.find_all('script')[0].text
    music_name=json.loads(data)["title"]
    json_text = json.loads(json_obj)
    original_lyrics=json_text['lrc']['lyric']
    translated_lyrics=json_text['tlyric']['lyric']
    return music_name,original_lyrics,translated_lyrics

# 网易云音乐：保存歌词按钮
async def saveLyrics(music_name, original_lyrics_text, translated_lyrics_text):
    lyrics_path = os.path.join(save_path, lyrics_directory_name, music_name)
    if not os.path.exists(lyrics_path):
        os.makedirs(lyrics_path)
        
    if original_lyrics_text:
        original_lrc_path = os.path.join(lyrics_path, '原文.lrc')
        with open(original_lrc_path, 'w', encoding='utf-8') as f_output:
            f_output.write(original_lyrics_text)
        
        srt_text = await run.io_bound(lrc2srt, original_lrc_path)
        original_srt_path = os.path.join(lyrics_path, '原文.srt')
        with open(original_srt_path, 'w', encoding='utf-8') as f_output:
            f_output.write(srt_text)
        
        ui.notify(f"唔姆…歌词给你放到这里吧：{original_lrc_path}(srt) o((>ω< ))o", position='top-right', type='positive')
    
    if translated_lyrics_text:
        translated_lrc_path = os.path.join(lyrics_path, '翻译.lrc')
        with open(translated_lrc_path, 'w', encoding='utf-8') as f_output:
            f_output.write(translated_lyrics_text)
        
        srt_text = await run.io_bound(lrc2srt, translated_lrc_path)
        translated_srt_path = os.path.join(lyrics_path, '翻译.srt')
        with open(translated_srt_path, 'w', encoding='utf-8') as f_output:
            f_output.write(srt_text)
        
        ui.notify("翻译的歌词也放在同一个地方哦 ο(=•ω＜=)ρ⌒☆", position='top-right', type='positive')

# LRC转SRT
def lrc2srt(input_file):
    lrc_file = open(input_file, encoding='utf-8')
    lrc_string = ''.join(lrc_file.readlines())
    lrc_file.close()

    subs = pylrc.parse(lrc_string)
    srt = subs.toSRT() # convert lrc to srt string

    return srt

# YouTube：歌词下载
async def getLyricsFromYoutube(url):
    n = ui.notification(message="等一等哦！正在下载歌词~ (o゜▽゜)o☆", position='top-right', timeout=None, spinner=True)
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            percent = strip_ansi(d.get('_percent_str', '0%').strip())
            speed = strip_ansi(d.get('_speed_str', 'N/A'))
            eta = strip_ansi(d.get('_eta_str', 'N/A'))
            title = d.get('filename', '').split(os.path.sep)[-1]
            n.message = f"[{percent} / {speed}] {title} ETA: {eta}"

    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': False,
        'subtitleslangs': ['all'],
        'skip_download': True,
        'outtmpl': os.path.join(save_path, lyrics_directory_name, '%(title)s', '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=False)
            title = info['title']
            await asyncio.to_thread(ydl.download, [url])
        
        n.dismiss()
        lyrics_dir = os.path.join(save_path, lyrics_directory_name, title)
        
        # 转换所有字幕为 SRT 格式
        for filename in os.listdir(lyrics_dir):
            file_path = os.path.join(lyrics_dir, filename)
            if filename.endswith('.vtt'):
                srt_path = os.path.splitext(file_path)[0] + '.srt'
                vtt = WebVTT().read(file_path)
                srt = pysrt.SubRipFile()
                for i, caption in enumerate(vtt):
                    item = pysrt.SubRipItem(index=i+1, 
                                            start=pysrt.SubRipTime.from_string(caption.start),
                                            end=pysrt.SubRipTime.from_string(caption.end),
                                            text=caption.text)
                    srt.append(item)
                srt.save(srt_path, encoding='utf-8')
                os.remove(file_path)  # 删除原始的 VTT 文件
            elif not filename.endswith('.srt'):
                os.remove(file_path)  # 删除非 SRT 文件
        
        downloaded_files = [f for f in os.listdir(lyrics_dir) if f.endswith('.srt')]
        
        if downloaded_files:
            file_list = "\n".join(downloaded_files)
            ui.notify(f"唔姆…歌词给你放到这里吧：{lyrics_dir}/{file_list} ( •̀ ω •́ )✧", position='top-right', type='positive')
        else:
            ui.notify("未找到可用的字幕 ＞︿＜", position='top-right', type='warning')
            shutil.rmtree(lyrics_dir)
    except Exception as e:
        n.dismiss()
        ui.notify(f"获取歌词失败: {str(e)} 〒▽〒", position='top-right', type='negative')


###### 翻译 ######
# SRT上传事件
async def srt_upload():
    srt_path = await run.io_bound(select_path, is_file=True, file_types=[('SRT字幕文件', '*.srt')])
    if srt_path.lower().endswith('.srt'):
        global deepl_result, gpt_result, srt_folder_path,srtfile_name, lines, subtitles, gpt_notification
        gpt_result = False
        deepl_result = False
        deepl_text.set_content("")
        gpt_text.set_content("")
        info_card_translate.set_visibility(False)
        
        srt_folder_path = os.path.dirname(srt_path)
        srtfile_name = os.path.basename(srt_path)
        with open(srt_path, 'r', encoding='utf-8-sig') as file:
            file_content = file.read()
            lines = file_content.splitlines()

        if deepl_switch.value:
            n = ui.notification(timeout=None, message="DeepL君在翻译啦，等一等哦~ []~(￣▽￣)~*", position='top-right', spinner=True)
            subtitles, deepl_result = await run.io_bound(DeepL, lines)
            n.dismiss()
            deepl_text.set_content('''<h2 class="text-2xl font-bold mb-4">DeepL君的翻译结果 (o゜▽゜)o☆</h3>
<pre style='white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word;'>'''+deepl_result+'</pre>')
            ui.notify("DeepL君翻译好啦！ (p≧w≦q)", position='top-right', type='positive')
            info_card_translate.set_visibility(True)

        if gpt_key:
            tips_content.set_content(f"{selected_model} 的价格为{price}美元每百万Token！ (≧∇≦)ﾉ</br>确定吗…？会不会太贵了 （＞人＜；）")
            result = await dialog
            if result == "Yes":
                gpt_notification = ui.notification(timeout=None, message=selected_model+"在帮忙啦！等等她吧~ ヾ(•ω•`)o", position='top-right', spinner=True)
                
                def update_notification(message):
                    gpt_notification.message=message

                gpt_result, translated_only, error = await run.io_bound(gpt_translate, file_content, selected_model, update_notification)
                if error:
                    ui.notify('呜呜 出错了：'+error+" ヾ(≧へ≦)〃", position='top-right', type='negative')
                    gpt_notification.dismiss()
                else:
                    gpt_text.set_content('<h2 class="text-2xl font-bold mb-4">'+selected_model+'''的翻译结果 ( •̀ ω •́ )y</h2>
    <pre style='white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word;'>'''+translated_only+'</pre>')
                    gpt_notification.dismiss()
                    ui.notify(selected_model+"翻译好了哦~ o(*￣▽￣*)ブ", position='top-right', type='positive')
                    info_card_translate.set_visibility(True)
    else:
        pass
        
# DeepL：翻译
def DeepL(lines):
    subtitles=[]
    subtitle_text=''
    for line in lines:
        line = line.strip()
        if not line: 
            pass
        elif '-->' in line:
            pass
        elif is_number(line): 
            pass
        else:  # 字幕文本行
            if line == "\ufeff1":
                pass
            else:
                subtitle_text +=  line + "\n" 
                subtitles.append(line.strip())
    translate_text=PyDeepLX.translate(subtitle_text, "JA", "ZH")
    return subtitles,translate_text

# DeepL：嵌回字幕
def replaceSub(translate_text,lines,subtitles):
    translated_lines = translate_text.strip().split('\n')
    translated_index = 0 
    for i in range(len(lines)):
        line = lines[i].strip()
        # 找到原文本，用翻译的替换
        if line in subtitles: 
            lines[i] = translated_lines[translated_index] + '\n'
            translated_index += 1
        else:
            lines[i] = line + '\n'
    return lines

# 模型金额查询
def inquiryAmount(target_model):
    for model_info in gpt_model_list:
        if model_info["model"] == target_model:
            return model_info["price"]
    return None

# 模型选择
async def selectModel(item):
    global selected_model,price
    selected_model=item
    price=await run.io_bound(inquiryAmount,selected_model)
    ui.notify("那个… "+selected_model+" 的价格为"+str(price)+"美元每百万Token！ (≧∇≦)ﾉ",position='top-right')

# GPT：调用
def gpt_translate(original_text, selected_model, progress_callback):
    try:
        subtitles, original_matches = extract_subtitles(original_text)
        translated_text = translate_subtitles(subtitles, selected_model, progress_callback)
        result = replace_subtitles(original_matches, translated_text)
        translated_only = get_translation_only(translated_text)
        return result, translated_only, None
    except Exception as e:
        return None, None, str(e)

# GPT：提取字幕
def extract_subtitles(srt_content):
    # 移除可能存在的 BOM
    srt_content = srt_content.encode('utf-8').decode('utf-8-sig')
    
    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n)(.*?)(?=\n\n|\Z)'
    matches = re.findall(pattern, srt_content, re.DOTALL)
    
    subtitles = [f"{number}. {text.strip()}" for number, _, text in matches]
    return subtitles, matches

# GPT：翻译
def translate_subtitles(subtitles, selected_model, progress_callback, batch_size=80):
    all_translated = []
    total_batches = (len(subtitles) + batch_size - 1) // batch_size

    prompt_template = """请将以下日语文本翻译成中文，严格遵守以下规则：
1. 保持原有的格式、序号和换行
2. 每个编号下的文本作为一个整体翻译
3. 不要添加任何解释或额外信息
4. 直接给出翻译结果，不要有其他输出
5. 删除说话人名字（如果有）
6. 不要合并句子
7. 必须保留每个条目的原始序号，格式为"数字."
8. 如果原文是空白的，翻译也应保持为空白

其中可能出现的人名以及中文翻译：
{gpt_character_prompt}

日语文本：
{subtitles_text}

请直接提供中文翻译，不要有任何其他解释或输出。务必保留每个条目的原始序号和格式。"""

    messages = [
        {"role": "system", "content": "你是一个精确的日中翻译器，只输出翻译结果，不做任何解释或添加。保持原有的格式、序号和换行，每个编号下的文本作为一个整体翻译，删除说话人名字，不合并句子。必须保留每个条目的原始序号。如果原文是空白的，翻译也应保持为空白。"}
    ]

    for i in range(0, len(subtitles), batch_size):
        current_batch = (i // batch_size) + 1
        progress_callback(f"{selected_model}在帮忙啦！等等她吧~ ヾ(•ω•`)o （{current_batch}/{total_batches}部分）")
        
        batch = subtitles[i:i+batch_size]
        subtitles_text = "\n".join(batch)
        full_prompt = prompt_template.format(subtitles_text=subtitles_text,gpt_character_prompt=gpt_character_prompt)

        messages.append({"role": "user", "content": full_prompt})

        response = client.chat.completions.create(
            model=selected_model,
            messages=messages
        )

        translated_text = response.choices[0].message.content
        all_translated.append(translated_text)

        messages.append({"role": "assistant", "content": translated_text})

    return "\n".join(all_translated)

# GPT：合成翻译字幕
def replace_subtitles(original_matches, translated_text):
    # 移除可能存在的 BOM
    translated_text = translated_text.encode('utf-8').decode('utf-8-sig')

    translated_dict = {}
    current_num = None
    current_translation = []
    
    for line in translated_text.split('\n'):
        if line.strip():
            if re.match(r'^[\W]?\d+\.', line):
                if current_num is not None:
                    translated_dict[current_num] = '\n'.join(current_translation)
                current_num = int(line.split('.')[0])
                current_translation = [line.split('.', 1)[1].strip()]
            else:
                current_translation.append(line.strip())
    
    if current_num is not None:
        translated_dict[current_num] = '\n'.join(current_translation)

    result_lines = []
    for number, time_code, _ in original_matches:
        result_lines.append(number)
        result_lines.append(time_code.strip())
        if int(number) in translated_dict:
            result_lines.append(translated_dict[int(number)])
        else:
            result_lines.append("")
        result_lines.append("")  # 添加空行分隔

    return '\n'.join(result_lines).strip()

# GPT：提取纯字幕
def get_translation_only(translated_text):
    translated_text = translated_text.encode('utf-8').decode('utf-8-sig')
    lines = translated_text.split('\n')
    translation_only = []
    for line in lines:
        if re.match(r'^\d+\.', line):
            translation_only.append(line.split('.', 1)[1].strip())
        elif line.strip():
            translation_only.append(line.strip())
    return '\n'.join(translation_only)

# 保存翻译按钮
async def saveTranslaion(deepl, gpt):
    if deepl:
        result = await run.io_bound(replaceSub, deepl, lines, subtitles)
        deepl_file_path = os.path.join(srt_folder_path, f'【DeepL】{srtfile_name}')
        with open(deepl_file_path, 'w', encoding='utf-8') as f:
            f.writelines(result)
            ui.notify(f"DeepL君的翻译结果被放到这里了哦：{deepl_file_path} o(￣▽￣)ｄ", position='top-right', type='positive')

    if gpt:
        # 构建完整的文件路径
        full_path = os.path.join(srt_folder_path, f"【{selected_model}】{srtfile_name}")

        # 使用 StringIO 处理文本
        buffer = StringIO(gpt)

        try:
            with open(full_path, 'w', encoding='utf-8', newline='') as f:
                for line in buffer:
                    f.write(line.rstrip('\r\n') + '\r\n')  # 确保每行以 CRLF 结束

            ui.notify(f"{selected_model}的翻译结果放在这里：{full_path} ヾ(•ω•`)o", 
                    position='top-right', 
                    type='positive')
        except Exception as e:
            ui.notify(f"呜呜 出问题了：{str(e)} ＞︿＜", 
                    position='top-right', 
                    type='negative')
        finally:
            buffer.close()


###### 压制 ######
# 压制按钮
async def handle_embedding():
    if not is_ffmpeg_installed():
        result = await ffmpeg_dialog
        if result == 'tutorial':
            ui.run_javascript('window.open("https://www.ffmpeg.org/", "_blank")')
        return
    embedding_button.disable()  # 禁用按钮
    try:
        await embeddingVideo(video_result.value, subtitle_result.value, cuda_switch.value)
    finally:
        embedding_button.enable()  # 重新启用按钮

# 压制
async def embeddingVideo(video_file, subtitle_file, cuda):
    if os.path.exists(video_file) and os.path.exists(subtitle_file):
        subfile_name, subfile_extension = os.path.splitext(subtitle_file)
        output_path = os.path.join(os.path.dirname(video_file), f"subed_output_{os.path.basename(video_file)}")

        shutil.copy(subtitle_file, "sub_tmp"+subfile_extension)

        n = ui.notification(message="视频正在努力压制中，请稍等一会儿哦~ (๑•̀ㅂ•́)و✧",position='top-right', timeout=None, spinner=True)
        await asyncio.sleep(0.1)  

        if cuda:
            cmd = [
                'ffmpeg',
                '-hwaccel', 'cuda',
                '-i', video_file,
                '-vf', f'subtitles=sub_tmp{subfile_extension}',
                '-c:v', 'h264_nvenc',
                '-preset', 'medium',
                '-crf', '23',
                '-c:a', 'copy',
                output_path,
                '-y'
            ]
        else:
            cmd = [
                'ffmpeg',
                '-i', video_file,
                '-vf', f'subtitles=sub_tmp{subfile_extension}',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-c:a', 'copy',
                output_path,
                '-y'
            ]

        try:
            async for message in run_ffmpeg_async(cmd):
                n.message = message
                await asyncio.sleep(0.1)  

            n.spinner = False
            if message== "耶！视频压制完成啦！你可以在原视频的文件夹里找到它哦~ ヽ(^◇^*)/":
                n.type="positive"
            else:
                n.type="negative"
            await asyncio.sleep(2)
            n.dismiss()
            os.remove("sub_tmp"+subfile_extension)
            return True

        except Exception as e:
            n.message = f'哎呀！出了点小问题呢: {str(e)}（＞人＜；）'
            n.type = 'negative'
            n.spinner = False
            await asyncio.sleep(2)
            n.dismiss()
            os.remove("sub_tmp"+subfile_extension)
            return False

    else:
        ui.notification('视频和字幕文件不存在？！(っ °Д °;)っ',position='top-right', type='negative')
        return False

# 调用FFmpeg
async def run_ffmpeg_async(cmd):
    def run_ffmpeg():
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW  # Prevents black window
        )
        for line in process.stdout:
            yield line
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)

    last_line = ""
    last_update_time = asyncio.get_event_loop().time()

    try:
        for line in await asyncio.to_thread(run_ffmpeg):
            line = line.strip()
            if line.startswith("frame=") and "fps" in line and "time=" in line and "bitrate=" in line and "speed=" in line:
                last_line = line

            current_time = asyncio.get_event_loop().time()
            if current_time - last_update_time > 0.5 and last_line:  # Update every 1 second
                formatted_line = format_ffmpeg_output(last_line)
                yield f'处理中~ ...(*￣０￣)ノ {formatted_line}'
                last_update_time = current_time
                await asyncio.sleep(0.1)  # Small delay to prevent UI freezing

        yield '耶！视频压制完成啦！你可以在原视频的文件夹里找到它哦~ ヽ(^◇^*)/'
    except subprocess.CalledProcessError as e:
        yield f'哎呀！出了点小问题呢: FFmpeg 进程返回 {e.returncode} （＞人＜；）'
    except Exception as e:
        yield f'哎呀！出了点小问题呢: run_ffmpeg_async: {str(e)} （＞人＜；）'

# 格式化FFmepg输出
def format_ffmpeg_output(line):
    parts = line.split()
    formatted_parts = []
    i = 0
    while i < len(parts):
        if "=" in parts[i]:
            key, value = parts[i].split("=")
            if key == "frame":
                value = value.strip()
                if not value:  # If value is empty, it's in the next part
                    value = parts[i+1].strip()
                    i += 1
                formatted_parts.append(f"已处理帧数:{value}")
            elif key == "fps":
                formatted_parts.append(f"帧率:{value}fps")
            elif key == "size":
                formatted_parts.append(f"已处理大小:{parts[i+1]}")
                i += 1
            elif key == "time":
                formatted_parts.append(f"已处理时间:{value}")
            elif key == "bitrate":
                formatted_parts.append(f"比特率:{parts[i+1]}")
                i += 1
            elif key == "speed":
                formatted_parts.append(f"速度:{value}")
        i += 1
    return " ".join(formatted_parts)


###### 设置 ######
# 保存按钮
def save():
    gpt_api_key_value = gpt_api_key_input.value
    if gpt_api_key_value.lower() == 'false':
        gpt_api_key_value = False

    new_settings = {
        'accept_gplv3': accept_gplv3,
        'save_path': save_path_input.value,
        'video': {
            'directory_name': video_dir_input.value,
            'cookies_file': cookies_file_input.value,
            'description_template': description_template_input.value,
            'tags_mapping': {m['key'].value: m['value'].value for m in tags_mapping_ui if m['key'].value and m['value'].value}
        },
        'lyrics': {
            'directory_name': lyrics_dir_input.value
        },
        'translator': {
            'gpt_api_base': gpt_api_base_input.value,
            'gpt_api_key': gpt_api_key_value,
            'gpt_character_prompt':gpt_character_prompt_input.value,
            'gpt_models': [{'model': m['model'].value, 'price': m['price'].value} for m in gpt_models_ui if m['model'].value and m['price'].value]
        }
    }
    save_settings(new_settings)
    ui.notify('设置已保存', position='top-right', type='positive')

# 写入配置文件
def save_settings(settings):
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)
    load_settings()
    if not gpt_key:
        model_selector.set_visibility(False)
    else:
        model_selector.set_visibility(True)

###### UI ######
# 自定义样式
ui.add_head_html('''
<style>
.q-tabs {
    display: none !important;
}
.tab-container {
    padding-bottom: 80px;
}
.fixed-nav-container {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1000;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
}

.fixed-nav {
    position: relative;
    transform: none;
    left: auto;
}
.gradient-border {
    background: white;
    border-radius: 30px;
    padding: 2px;
    background-image: linear-gradient(to right, #f19ec2, #7fcef4);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08);
}
.nav-content {
    background: white;
    border-radius: 28px;
    padding: 8px 16px;
    display: flex;
    align-items: center;
}
.nav-btn {
    transition: all 0.3s ease;
    border-radius: 20px;
    padding: 5px 10px;
}
.nav-btn.active {
    background-color: #E0E0E0 !important;
}
.nav-btn .q-icon {
    margin-right: 5px;
}
.custom-btn {
    display: flex;
    align-items: center;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 14px;
    color: black;
}
.custom-btn .avatar {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    margin-right: 8px;
}
</style>

<script>
function activateNavButton(buttonIndex) {
    const buttons = document.querySelectorAll('.nav-btn');
    buttons.forEach((btn, index) => {
        if (index === buttonIndex) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}
</script>
''')

# 多标签页
tabs = ui.tabs().classes('w-full tab-container')
ui.tab('视频')
ui.tab('歌词')
ui.tab('翻译')
ui.tab('字幕')
ui.tab('设置')

# 弹窗
with ui.dialog() as ffmpeg_dialog, ui.card():
    ui.label('未检测到 FFmpeg (≧﹏ ≦)').style('font-size:24px')
    ui.html('''
YouTube和ニコニコ動画现均已<b>将音画内容分开储存</b>，下载需要 FFmpeg 才能合并音轨和视轨。压制字幕也依赖FFmpeg<br>
Kotonoha Toolkit已经不内置FFmpeg，需要您自行下载！<br><br>
<i>FFmpeg 是一个开放源代码的自由软件，可以执行音频和视频多种格式的录影、转换、串流功能，
包含了libavcodec——这是一个用于多个项目中音频和视频的解码器函数库，
以及libavformat——一个音频与视频格式转换函数库。</i>
''')
    with ui.row():
        ui.button('FFmpeg官网', on_click=lambda: ffmpeg_dialog.submit('tutorial'))
        ui.button('取消', on_click=lambda: ffmpeg_dialog.submit('cancel'))

with ui.dialog() as dialog, ui.card():
                ui.label('哇！找到了GPT Key！要不要请GPT翻译呢？ o(*￣▽￣*)o').style('font-size:24px')
                tips_content = ui.html()
                with ui.row():
                    ui.button('好呀好呀', on_click=lambda: dialog.submit('Yes')).classes('mr-4').props('icon=check')
                    ui.button('算了', on_click=lambda: dialog.submit('No')).props('icon=close')

dialog_gplv3 = ui.dialog().props('persistent')
with dialog_gplv3, ui.card():
    ui.label("软件许可协议 (GPL v3)").style('font-size:24px')
    ui.label('根据GNU通用公共许可证第三版（GPLv3），本软件的使用受到特定条款的约束。我们要求所有用户在使用本软件之前，仔细阅读并遵守GPLv3协议的所有规定。')
    with ui.scroll_area().classes('h-96 w-full'):
        ui.markdown(gpl_v3_text)
    with ui.row().classes('w-full justify-end'):
        ui.button('接受', on_click=lambda: accept_gplv3_button())
        ui.button('拒绝', on_click=sys.exit, color='red')

#主界面
with ui.tab_panels(tabs, value='视频').classes('w-full'):
    with ui.tab_panel('视频'):
        with ui.column().classes('w-full p-4'):
            ui.label('视频下载').classes('text-4xl font-bold mb-4')
            
            with ui.row().classes('w-full items-center mb-4 gap-4'):
                video_url = ui.input('视频链接', 
                                     validation={'哎呀，这不是油管或N站的链接呢 (´･ω･`)': lambda value: getVideoPlatform(value)},
                                     on_change=lambda: updateButtonStatus(video_url.value)).classes('flex-grow')
                get_info_button = ui.button('获取信息', on_click=lambda: getInfomation(video_url.value)).classes('w-1/4').props('icon=info')
            
            with ui.card().classes('w-full p-4') as info_card:
                with ui.row().classes('w-full items-center justify-between'):
                    ui.label('视频信息').classes('text-2xl font-bold')
                    with ui.row().classes('gap-2'):
                        ui.button('保存信息到本地', on_click=lambda: saveCover(title_path, thumbnail_url)).classes('text-sm').props('icon=save')
                        downloadButton = ui.button('下载视频', on_click=lambda: downloadVideoButton(title_path, video_url.value)).classes('text-sm').props('icon=download')
                
                with ui.row().classes('w-full mt-4'):
                    with ui.column().classes('w-1/3'):
                        cover = ui.image('./static/loading.gif')
                    with ui.column().classes('w-2/3 pl-4'):
                        info = ui.markdown('视频的信息马上就来啦~ (≧▽≦)').classes('w-full')

    with ui.tab_panel('歌词'):
        with ui.column().classes('w-full p-4'):
            ui.label('歌词下载').classes('text-4xl font-bold mb-4')
            with ui.row().classes('w-full items-center mb-4 gap-4'):
                music_url = ui.input('音乐链接', 
                                     validation={'哎呀，这不是油管或网易云的链接呢 (´･ω･`)': lambda value: getMusicPlatform(value)},
                                     on_change=lambda: updateMusicButtonStatus(music_url.value)).classes('flex-grow')
                get_lyrics_button = ui.button('获取歌词', on_click=lambda: getLyrics(music_url.value)).classes('w-1/4').props('icon=music_note')

            with ui.card().classes('w-full p-4') as info_card_music:
                with ui.row().classes('w-full items-center justify-between'):
                    music_title = ui.label('歌词').classes('text-2xl font-bold')
                    ui.button('保存到本地', on_click=lambda: saveLyrics(music_name_text, original_lyrics_text, translated_lyrics_text)).classes('text-sm').props('icon=save')
                
                with ui.row().classes('w-full').style('display: flex; flex-direction: row;'):
                    with ui.column().classes('w-1/2 pr-2').style('flex: 1; min-width: 0;'):
                        original_lyrics = ui.html().style('width: 100%;')
                    with ui.column().classes('w-1/2 pl-2').style('flex: 1; min-width: 0;'):
                        translate_lyrics = ui.html().style('width: 100%;')

    with ui.tab_panel('翻译'):
        with ui.column().classes('w-full p-4'):
            ui.label('剧本翻译').classes('text-4xl font-bold mb-2')
          
            with ui.row().classes('w-full items-center mb-4'):
                with ui.column().classes('w-1/2'):
                    with ui.row().classes('items-center w-full') as model_selector:
                        ui.label('GPT模型选择').classes('mr-2')
                        ui.select(options=gpt_model_names, with_input=True,
                                on_change=lambda e: selectModel(e.value), value=selected_model).classes('flex-grow')
                deepl_switch = ui.switch('启用DeepL翻译')

            translate_button = ui.button('选择字幕文件', on_click=lambda: srt_upload()).props('icon=upload').classes('w-full')

            with ui.card().classes('w-full p-4 mb-4') as info_card_translate:
                with ui.row().classes('w-full items-center justify-between'):
                    ui.label('翻译').classes('text-2xl font-bold')
                    ui.button('保存到本地', on_click=lambda: saveTranslaion(deepl_result, gpt_result)).classes('text-sm').props('icon=save')
                
                with ui.row().classes('w-full').style('display: flex; flex-direction: row;'):
                    with ui.column().classes('w-1/2 pr-2').style('flex: 1; min-width: 0;'):
                        deepl_text = ui.html().style('width: 100%;')
                    with ui.column().classes('w-1/2 pl-2').style('flex: 1; min-width: 0;'):
                        gpt_text = ui.html().style('width: 100%;')

    with ui.tab_panel('字幕'):
        with ui.column().classes('w-full p-4'):
            ui.label('字幕提取、压制').classes('text-4xl font-bold mb-2')
            with ui.row().style("flex-direction:column; align-self:left; width: 100%; height: 100%; padding: 10px;").classes('flex-left'):
                with ui.row().classes('items-center w-full').style('flex-direction:row'):
                    video_button = ui.button('选择视频文件', on_click=lambda: handle_path_selection(video_result, is_file=True, file_types=[('视频文件', '*.mp4 *.webm *.avi')])).props('icon=videocam')
                    video_result = ui.input(label='已选视频文件').props('readonly').classes('flex-grow')

                with ui.row().classes('items-center  w-full mt-4').style('flex-direction:row'):
                    subtitle_button = ui.button('选择字幕文件', on_click=lambda: handle_path_selection(subtitle_result, is_file=True, file_types=[('字幕文件', '*.ass *.srt')])).props('icon=subtitles')
                    subtitle_result = ui.input(label='已选字幕文件').props('readonly').classes('flex-grow')
                
                with ui.row().classes('items-center w-full mt-4').style('flex-direction:row'):
                    extract_button = ui.button('提取字幕', on_click=lambda: ui.notify("此功能错误率太大已被移除，可以试试Whisper或CupCut字幕提取插件哦 (´；ω；`) ",position='top-right',type='negative')).classes('flex-grow').props('icon=subtitles')
                    lang_select = ui.select(["日本語", "English", "中文"], value="日本語").classes('w-1/5 ml-4')

                with ui.row().classes('items-center w-full mt-4').style('flex-direction:row'):
                    embedding_button = ui.button('压制', on_click=lambda: handle_embedding()).classes('flex-grow').props('icon=merge_type')
                    cuda_switch = ui.switch('CUDA NVENC加速（Nvidia显卡）').classes('w-1/5 ml-4')

    with ui.tab_panel('设置'):
        with ui.column().classes('w-full p-4'):
            ui.label('设置').classes('text-4xl font-bold mb-2')
                 
            ui.button('保存设置', on_click=save).props('icon=save').style('position: fixed; top: 40px; right: 40px; z-index: 1000;')
            with ui.row().classes('items-center w-full mb-2').style('flex-direction:row'):
                    save_path_input = ui.input('保存路径', value=save_path).classes('flex-grow')
                    video_button = ui.button('选择保存路径', on_click=lambda: handle_path_selection(save_path_input, is_file=False)).props('icon=folder')
            
            ui.label('视频设置').classes('text-xl font-bold mb-2')
            video_dir_input = ui.input('视频目录名', value=video_directory_name).classes('w-full mb-2')
            with ui.row().classes('items-center w-full mb-2').style('flex-direction:row'):
                    cookies_file_input = ui.input('Cookies 文件路径', value=cookies_file).classes('flex-grow')
                    video_button = ui.button('选择 Cookies 文件', on_click=lambda: handle_path_selection(cookies_file_input, is_file=True, file_types=[('QAQ', '*.txt')])).props('icon=insert_drive_file')
            description_template_input = ui.textarea('简介模板', value=description_template).classes('w-full mb-2')
            
            with ui.expansion('标签匹配', icon='label').classes('w-full mb-2'):
                tags_mapping_ui = []
                for key, value in tags_mapping.items():
                    with ui.row().classes('w-full gap-2') as row:
                        key_input = ui.input('原标签', value=key).classes('flex-grow')
                        value_input = ui.input('映射标签', value=value).classes('flex-grow')
                        mapping = {'key': key_input, 'value': value_input, 'row': row}
                        tags_mapping_ui.append(mapping)
                        ui.button('删除', on_click=lambda m=mapping: (m['row'].delete(), tags_mapping_ui.remove(m))).props('icon=delete')
                
                def add_tag_mapping():
                    with ui.row().classes('w-full gap-2') as new_row:
                        key_input = ui.input('原标签').classes('flex-grow')
                        value_input = ui.input('映射标签').classes('flex-grow')
                        new_mapping = {'key': key_input, 'value': value_input, 'row': new_row}
                        tags_mapping_ui.append(new_mapping)
                        ui.button('删除', on_click=lambda m=new_mapping: (m['row'].delete(), tags_mapping_ui.remove(m))).props('icon=delete')
                
                ui.button('添加标签匹配', on_click=add_tag_mapping).props('icon=add')
            
            ui.label('歌词设置').classes('text-xl font-bold mb-2')
            lyrics_dir_input = ui.input('歌词目录名', value=lyrics_directory_name).classes('w-full mb-2')
            
            ui.label('翻译设置').classes('text-xl font-bold mb-2')
            gpt_api_base_input = ui.input('GPT API Base URL', value=gpt_api_base).classes('w-full mb-2')
            gpt_api_key_input = ui.input('GPT API Key', value=str(gpt_key)).classes('w-full mb-2')
            gpt_character_prompt_input = ui.textarea('GPT 人物提示词', value=gpt_character_prompt).classes('w-full mb-2')
            
            with ui.expansion('GPT 模型', icon='model_training').classes('w-full mb-2'):
                gpt_models_ui = []
                for model in gpt_model_list:
                    with ui.row().classes('w-full gap-2') as row:
                        model_input = ui.input('模型名称', value=model['model']).classes('flex-grow')
                        price_input = ui.number('价格（美元/每百万Token）', value=model['price']).classes('flex-grow')
                        model_obj = {'model': model_input, 'price': price_input, 'row': row}
                        gpt_models_ui.append(model_obj)
                        ui.button('删除', on_click=lambda m=model_obj: (m['row'].delete(), gpt_models_ui.remove(m))).props('icon=delete')
                
                def add_gpt_model():
                    with ui.row().classes('w-full gap-2') as new_row:
                        model_input = ui.input('模型名称').classes('flex-grow')
                        price_input = ui.number('价格（美元/每百万Token）').classes('flex-grow')
                        new_model = {'model': model_input, 'price': price_input, 'row': new_row}
                        gpt_models_ui.append(new_model)
                        ui.button('删除', on_click=lambda m=new_model: (m['row'].delete(), gpt_models_ui.remove(m))).props('icon=delete')
                
                ui.button('添加 GPT 模型', on_click=add_gpt_model).props('icon=add')

# 导航栏
with ui.element('div').classes('fixed-nav-container'):
    with ui.element('div').classes('fixed-nav'):
        with ui.element('div').classes('gradient-border'):
            with ui.element('div').classes('nav-content'):
                ui.button('视频', on_click=lambda: (tabs.set_value('视频'), ui.run_javascript('activateNavButton(0)')), icon='videocam').props('flat color=black').classes('nav-btn')
                ui.button('歌词', on_click=lambda: (tabs.set_value('歌词'), ui.run_javascript('activateNavButton(1)')), icon='music_note').props('flat color=black').classes('nav-btn')
                ui.button('翻译', on_click=lambda: (tabs.set_value('翻译'), ui.run_javascript('activateNavButton(2)')), icon='translate').props('flat color=black').classes('nav-btn')
                ui.button('字幕', on_click=lambda: (tabs.set_value('字幕'), ui.run_javascript('activateNavButton(3)')), icon='closed_caption').props('flat color=black').classes('nav-btn')
                ui.button('设置', on_click=lambda: (tabs.set_value('设置'), ui.run_javascript('activateNavButton(4)')), icon='settings').props('flat color=black').classes('nav-btn')

    # 作者信息
    with ui.element('div').classes('fixed-nav'):
        with ui.element('div').classes('gradient-border'):
            with ui.element('div').classes('nav-content'):
                ui.button('源代码', on_click=lambda: (ui.run_javascript('window.open("https://github.com/Quasar-Fansub/kotonoha_toolkit", "_blank")')), icon='code').props('flat color=black').classes('nav-btn')

# 初始化界面
get_info_button.disable()
get_lyrics_button.disable()
info_card.set_visibility(False)
info_card_music.set_visibility(False)
info_card_translate.set_visibility(False)
if not gpt_key:
    model_selector.set_visibility(False)

@app.on_connect
async def auto_check_update(client):
    ui.run_javascript('activateNavButton(0)')
    if accept_gplv3 :
        pass
    else:
        await dialog_gplv3.open()

# 启动服务
ui.run(
    title='Kotonoha Toolkit', 
    reload=False,
    native=True,
    window_size=(1200, 900)
)