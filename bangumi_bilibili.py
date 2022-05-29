import requests
import streamlit as st
import difflib
import re
from PIL import Image
from io import BytesIO

def get_user_collection(vmid,sessdata,type=1,pn=1,ps=30):
    url='https://api.bilibili.com/x/space/bangumi/follow/list'
    parameter={'type':type,'vmid':vmid,'pn':pn,'ps':ps}
    cookies={'SESSDATA':sessdata}
    responce=requests.get(url=url,params=parameter,cookies=cookies).json()

    data=responce['data']['list']
    total=responce['data']['total']
    if total>ps:
        for i in range(total//ps):
            pn+=1
            parameter={'type':type,'vmid':vmid,'pn':pn,'ps':ps}
            responce=requests.get(url=url,params=parameter,cookies=cookies).json()
            data+=responce['data']['list']
    return data,total
#search_item
def search_item(subject_name,type=2,start=0,max_results=25):

    header={'User-Agent':'bgm22896274e3b69b06c'}
    url="https://api.bgm.tv/search/subject/"+subject_name+"?type="+str(type)+"&responseGroup=medium&start"+str(start)+"&max_results="+str(max_results)
    responce=requests.get(url=url,headers=header).json()
    data=responce['list']
    return data,len(data)

def callback():

    header={'User-Agent':'bgm22896274e3b69b06c','Authorization':'Bearer '+st.session_state.access_token}
    status=["wish","collect","do","hold","dropped"]
    for i in range(st.session_state.total):
        select_name=st.session_state['chosen_name_'+str(i)].split('_')
        watched_eps=st.session_state['chosen_eps_'+str(i)]
        body={"status": 'do'}
        st.info("正在更新收藏"+select_name[0])
        url="https://api.bgm.tv/collection/"+select_name[1]+"/update"
        r=requests.post(url=url,data=body,headers=header).json()
        try:
            st.success("成功更新"+r['user']['nickname']+'收藏')
        except:
            st.warning("未授权，请检查bearer token！")
        
        st.info("正在更新"+select_name[0]+",收视进度为第"+str(watched_eps)+"话")
        url='https://api.bgm.tv/subject/'+select_name[1]+'/update/watched_eps'
        param={'watched_eps':watched_eps}
        r=requests.post(url=url,params=param,headers=header).json()
        if r['code']==202:
            st.success("成功！")
        else:
            st.error("未授权,请检查bearer token")

with st.sidebar:
    uid=st.text_input("BiliBili uid:")
    sessdata=st.text_input("Cookie SESSDATA:")
    access_token=st.text_input("Bearer Token:")
    button=st.button("Submit")

col=list()

if 'total' not in st.session_state:
    st.session_state.total=0
if 'access_token' not in st.session_state:
    st.session_state.access_token=access_token

if button:
    with st.form("Bangumi"):
        info,total=get_user_collection(uid,sessdata)

        for i in range(total):
            title=info[i]['title']
        
            search_title=re.sub(u"([^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a\u0020])","",info[i]['series']['title'])
        
            bangumi,num=search_item(search_title)

            diff=list()

            for j in range(num):
                if bangumi[j]['name_cn']:
                    name_cn=bangumi[j]['name_cn']
                name=bangumi[j]['name']

                diff_name=difflib.SequenceMatcher(None,title,name).ratio()
                diff_namecn=difflib.SequenceMatcher(None,title,name_cn).ratio()
                if diff_name>diff_namecn:
                    diff.append([diff_name,name+'_'+str(bangumi[j]['id'])])
                else:
                    diff.append([diff_namecn,name_cn+'_'+str(bangumi[j]['id'])])

            diff.sort(key=lambda x: x[0],reverse=True)


            col.append(st.columns([1,2]))
            col[i][0].image(Image.open(BytesIO(requests.get(info[i]['cover']).content)))
            col[i][1].subheader(title)
            try:
                watched_eps=int(re.findall(r'\d+',info[i]['progress'])[0])
                col[i][1].markdown("#### "+info[i]['progress'])
            except Exception:
                col[i][1].markdown("#### 未观看")
                watched_eps=0

            options=[i[1] for i in diff]

            chosen_name=col[i][1].selectbox(label='请选择Bangumi上对应的番剧',options=options,key='chosen_name_'+str(i))

            if watched_eps<=info[i]['total_count']:
                chosen_eps=col[i][1].number_input(label='请选择看到的集数',min_value=0,max_value=info[i]['total_count'],value=watched_eps,step=1,key='chosen_eps_'+str(i))
            else:
                chosen_eps=col[i][1].number_input(label='请选择看到的集数',min_value=0,max_value=watched_eps,value=watched_eps,step=1,key='chosen_eps_'+str(i))
        
        st.session_state.total=total
        st.session_state.access_token=access_token

        submitted = st.form_submit_button(label="确认提交",on_click=callback)