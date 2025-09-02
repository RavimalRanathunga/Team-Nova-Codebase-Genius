impl managerAgent.route
{
    #check whether the repo is already cloned or not
    if os.path.exists(self.repo_path)
    {
        response:AgentType = self.decide(self.message,visitor.get_last_five_messages());
        print(f"Navigating to {response}");
        
        visitor.chat_history.append({"action":f"Navigating to {response} as the repository is already cloned."});

        visit[-->](`?Agent)(?agent_type==response);
    }
    else
    {
        repository_clone_message:str = self.clone_github_repository(self.github_url,self.repo_path);
        response:AgentType = self.decide(self.message,visitor.get_last_five_messages());
        print(f"Navigating to {response}");

        visitor.chat_history.append({"action":repository_clone_message + f" Navigating to {response}."});

        visit[-->](`?Agent)(?agent_type==response);
    }
}

impl repoMapperAgent.map_repo
{
    print("Building Repository Folder Structure...");
    gitignore:PathSpec = load_gitignore(self.repo_path);#get the .gitignore patterns
    structure:Dict[str,Any] = build_structure(self.repo_path,gitignore);
    folders_dict:dict[str,str] = get_folder_dict(self.repo_path,gitignore);
    readme_contents:dict[str,str] = extract_readmes(structure);
    
    print("Generating README Files Summeries...");
    readme_file_summeries:dict[str,str] = self.generate_readme_files_summeries(readme_contents);

    visitor.code_structure = structure;
    visitor.folders_dict = folders_dict;
    visitor.readme_contents = readme_file_summeries;
    visitor.chat_history.append({"action":"Generate the repo structure and Generate summeries for readme.md files"});

    visit[<--];
}

impl codeAnalyzerAgent.analyze_code
{
    analysis:dict = traverse_and_parse(visitor.code_structure);
    print("Code Analysis Complete.");

    visitor.chat_history.append({"action":"Code Analysis Complete."});
    visitor.code_analysis = analysis;

    visit[<--];
}

impl docGenieAgent.generate_docs
{
    if not os.path.exists(self.doc_path)
    {
        os.mkdir(self.doc_path);

        print(self.generate_readme_files_for_each_folder(visitor.folders_dict,visitor.readme_contents,self.doc_path,visitor.code_analysis,dict_to_tree(visitor.code_structure),instruction_to_generate_code_structure_mermaid_diagram));

        print(self.generate_class_diagram_as_an_image(self.doc_path,visitor.code_analysis,instruction_to_generate_class_diagram_mermaid_diagram));
        print(self.generate_sequence_diagram_as_an_image(self.doc_path,visitor.code_analysis,instruction_to_generate_sequence_diagram_mermaid_diagram));

        print(self.update_main_readme(self.doc_path,visitor.readme_contents));
        print("Documentation Generation Complete.");

        visitor.chat_history.append({"action":"Documentation Generation Complete."});
        disengage;
    }
    else
    {
        print(self.generate_readme_files_for_each_folder(visitor.folders_dict,visitor.readme_contents,self.doc_path,visitor.code_analysis,dict_to_tree(visitor.code_structure),instruction_to_generate_code_structure_mermaid_diagram));
        
        print(self.generate_class_diagram_as_an_image(self.doc_path,visitor.code_analysis,instruction_to_generate_class_diagram_mermaid_diagram));
        print(self.generate_sequence_diagram_as_an_image(self.doc_path,visitor.code_analysis,instruction_to_generate_sequence_diagram_mermaid_diagram));

        print(self.update_main_readme(self.doc_path,visitor.readme_contents));
        print("Documentation Generation Complete.");

        visitor.chat_history.append({"action":"Documentation Generation Complete."});
        disengage;
    }
}