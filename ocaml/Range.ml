open Core;;

(* A range is a string of the type:
 * 
 * "[36-53,72-107,126-131]"
 *
 * that should represent the list of integers
 * [ 37 ; 37 ; 38 ; ... ; 52 ; 53 ; 72 ; 73 ; ... ; 106 ; 107 ; 126 ; 127 ; ...
 * ; 130 ; 131 ]
 *
 * or it can be an integer
*)


type t = int list [@@deriving sexp]

let expand_range r =
  match String.lsplit2 ~on:'-' r with
  | Some (s, f) ->
      begin
        let start = Int.of_string s
        and finish =  Int.of_string f
        in
        assert (start <= finish) ;
        let rec do_work = function
          | i when i=finish -> [ i ]
          | i     -> i::(do_work (i+1))
        in do_work start
      end
  | None -> 
      begin
        match r with
          | "" -> []
          | _  -> [Int.of_string r] 
      end
;;

let of_string s =
  match s.[0] with
  | '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' ->
      [ int_of_string s ]
  | _ ->
    assert (s.[0] = '[') ;
    assert (s.[(String.length s)-1] = ']') ;
    let s = String.sub s 1 ((String.length s) - 2) in
    let l = String.split ~on:',' s in
    let l = List.map ~f:expand_range l in
  List.concat l |> List.dedup ~compare:Int.compare |> List.sort ~cmp:Int.compare
;;

let to_string l =
  let rec do_work buf symbol = function
    | [] -> buf
    | a::([] as t) -> 
          do_work (buf^symbol^(Int.to_string a)) "" t
    | a::(b::q as t) ->
        if (b-a = 1) then
          do_work buf "-" t
        else
          do_work (buf^symbol^(Int.to_string a)^","^(Int.to_string b)) "" t
  in
  let result = 
    match l with
    | [] ->
        "[]"
    | h::t  ->
        do_work ("["^(Int.to_string h)) "" l in
  (String.sub result 0 ((String.length result)))^"]"
;;

let test_module () =
  let s = "[72-107,36-53,126-131]" in
  let l = of_string s in
  print_string s ; Out_channel.newline stdout ;
  List.iter ~f:(fun x -> Printf.printf "%d, " x) l ; Out_channel.newline stdout ;
  to_string l |> print_string ;  Out_channel.newline stdout
;;

