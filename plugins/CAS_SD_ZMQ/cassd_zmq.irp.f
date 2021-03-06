program cassd_zmq
  implicit none
  integer                        :: i,j,k
  double precision, allocatable  :: pt2(:)
  integer                        :: degree
  integer                        :: n_det_before, to_select
  double precision               :: threshold_davidson_in
  double precision               :: error(N_states)
  
  allocate (pt2(N_states))

  double precision               :: hf_energy_ref
  logical                        :: has
  integer                        :: N_states_p
  character*(512)                :: fmt
  character*(8) :: pt2_string

  pt2 = -huge(1.d0)
  error = 0.d0
  threshold_davidson_in = threshold_davidson
  threshold_davidson = threshold_davidson_in * 100.d0
  SOFT_TOUCH threshold_davidson

  if (do_pt2) then
    pt2_string = '        '
  else
    pt2_string = '(approx)'
  endif

  call diagonalize_CI
  call save_wavefunction
  
  call ezfio_has_hartree_fock_energy(has)
  if (has) then
    call ezfio_get_hartree_fock_energy(hf_energy_ref)
  else
    hf_energy_ref = ref_bitmask_energy
  endif

  if (N_det > N_det_max) then
    psi_det = psi_det_sorted
    psi_coef = psi_coef_sorted
    N_det = N_det_max
    soft_touch N_det psi_det psi_coef
    call diagonalize_CI
    call save_wavefunction
    print *,  'N_det    = ', N_det
    print *,  'N_states = ', N_states
    do k=1,N_states
      print*,'State ',k
      print *,  'PT2      = ', pt2(k)
      print *,  'E        = ', CI_energy(k)
      print *,  'E+PT2    = ', CI_energy(k) + pt2(k)
      print *,  '-----'
    enddo
  endif
  double precision               :: E_CI_before(N_states)
  
  
  if (.True.) then ! Avoid pre-calculation of CI_energy
    E_CI_before(1:N_states) = CI_energy(1:N_states)
  endif
  n_det_before = 0

  double precision :: correlation_energy_ratio
  correlation_energy_ratio = 0.d0

  if (.True.) then ! Avoid pre-calculation of CI_energy
    do while (                                                         &
          (N_det < N_det_max) .and.                                    &
          (maxval(abs(pt2(1:N_states))) > pt2_max) .and.               &
          (correlation_energy_ratio <= correlation_energy_ratio_max)    &
          )
       write(*,'(A)')  '--------------------------------------------------------------------------------'


      correlation_energy_ratio = (CI_energy(1) - hf_energy_ref)  /     &
                      (E_CI_before(1) + pt2(1) - hf_energy_ref)
      correlation_energy_ratio = min(1.d0,correlation_energy_ratio)


      print *,  'N_det             = ', N_det
      print *,  'N_states          = ', N_states
      print*,   'correlation_ratio = ', correlation_energy_ratio

      do k=1, N_states
        print*,'State ',k
        print *,  'PT2             = ', pt2(k)
        print *,  'E               = ', CI_energy(k)
        print *,  'E(before)+PT2   = ', E_CI_before(k)+pt2(k)
      enddo

      print *,  '-----'
      if(N_states.gt.1)then
        print*,'Variational Energy difference'
        do i = 2, N_states
          print*,'Delta E = ',CI_energy(i) - CI_energy(1)
        enddo
      endif
      if(N_states.gt.1)then
        print*,'Variational + perturbative Energy difference'
        do i = 2, N_states
          print*,'Delta E = ',E_CI_before(i)+ pt2(i) - (E_CI_before(1) + pt2(1))
        enddo
      endif
      E_CI_before(1:N_states) = CI_energy(1:N_states)

      n_det_before = N_det
      to_select = N_det
      to_select = max(N_det, to_select)
      to_select = min(to_select, N_det_max-n_det_before)
      call ZMQ_selection(to_select, pt2)
      
      N_states_p = min(N_det,N_states)

      print *, ''
      print '(A,I12)',  'Summary at N_det = ', N_det
      print '(A)',      '-----------------------------------'
      print *, ''
      call write_double(6,correlation_energy_ratio, 'Correlation ratio')
      print *, ''

      write(fmt,*) '(''# ============'',', N_states_p, '(1X,''=============================''))'
      write(*,fmt)
      write(fmt,*) '(12X,', N_states_p, '(6X,A7,1X,I6,10X))'
      write(*,fmt) ('State',k, k=1,N_states_p)
      write(fmt,*) '(''# ============'',', N_states_p, '(1X,''=============================''))'
      write(*,fmt)
      write(fmt,*) '(A12,', N_states_p, '(1X,F14.8,15X))'
      write(*,fmt) '# E          ', E_CI_before(1:N_states_p)
      if (N_states_p > 1) then
        write(*,fmt) '# Excit. (au)', E_CI_before(1:N_states_p)-E_CI_before(1)
        write(*,fmt) '# Excit. (eV)', (E_CI_before(1:N_states_p)-E_CI_before(1))*27.211396641308d0
      endif
      write(fmt,*) '(A12,', 2*N_states_p, '(1X,F14.8))'
      write(*,fmt) '# PT2'//pt2_string, (pt2(k), error(k), k=1,N_states_p)
      write(*,'(A)') '#'
      write(*,fmt) '# E+PT2      ', (E_CI_before(k)+pt2(k),error(k), k=1,N_states_p)
      if (N_states_p > 1) then
        write(*,fmt) '# Excit. (au)', ( (E_CI_before(k)+pt2(k)-E_CI_before(1)-pt2(1)), &
          dsqrt(error(k)*error(k)+error(1)*error(1)), k=1,N_states_p)
        write(*,fmt) '# Excit. (eV)', ( (E_CI_before(k)+pt2(k)-E_CI_before(1)-pt2(1))*27.211396641308d0, &
          dsqrt(error(k)*error(k)+error(1)*error(1))*27.211396641308d0, k=1,N_states_p)
      endif
      write(fmt,*) '(''# ============'',', N_states_p, '(1X,''=============================''))'
      write(*,fmt)
      print *,  ''

      print *,  'N_det             = ', N_det
      print *,  'N_states          = ', N_states
      print*,   'correlation_ratio = ', correlation_energy_ratio

      do k=1, N_states_p
        print*,'State ',k
        print *,  'PT2             = ', pt2(k)
        print *,  'E               = ', E_CI_before(k)
        print *,  'E+PT2'//pt2_string//'   = ', E_CI_before(k)+pt2(k), ' +/- ', error(k)
      enddo

      print *,  '-----'
      if(N_states.gt.1)then
        print *, 'Variational Energy difference (au | eV)'
        do i=2, N_states_p
          print*,'Delta E = ', (E_CI_before(i) - E_CI_before(1)), &
            (E_CI_before(i) - E_CI_before(1)) * 27.211396641308d0
        enddo
        print *,  '-----'
        print*, 'Variational + perturbative Energy difference (au | eV)'
        do i=2, N_states_p
          print*,'Delta E = ', (E_CI_before(i)+ pt2(i) - (E_CI_before(1) + pt2(1))), &
            (E_CI_before(i)+ pt2(i) - (E_CI_before(1) + pt2(1))) * 27.211396641308d0
        enddo
      endif

      PROVIDE  psi_coef
      PROVIDE  psi_det
      PROVIDE  psi_det_sorted

      if (N_det >= N_det_max) then
        threshold_davidson = threshold_davidson_in
      end if
      call diagonalize_CI
      call save_wavefunction
      call ezfio_set_cas_sd_zmq_energy(CI_energy(1))
    enddo
  endif

  if (N_det < N_det_max) then
      threshold_davidson = threshold_davidson_in
      call diagonalize_CI
      call save_wavefunction
      call ezfio_set_cas_sd_zmq_energy(CI_energy(1))
  endif

  integer :: exc_max, degree_min
  exc_max = 0
  print *,  'CAS determinants : ', N_det_cas
  do i=1,min(N_det_cas,20)
    do k=i,N_det_cas
      call get_excitation_degree(psi_cas(1,1,k),psi_cas(1,1,i),degree,N_int)
      exc_max = max(exc_max,degree)
    enddo
    print *,  psi_cas_coef(i,:)
    call debug_det(psi_cas(1,1,i),N_int)
    print *,  ''
  enddo
  print *,  'Max excitation degree in the CAS :', exc_max

  if(do_pt2)then
    print*,'Last iteration only to compute the PT2'
    threshold_selectors = max(threshold_selectors,threshold_selectors_pt2)
    threshold_generators = max(threshold_generators,threshold_generators_pt2)
    TOUCH threshold_selectors threshold_generators
    E_CI_before(1:N_states) = CI_energy(1:N_states)
    call ZMQ_selection(0, pt2)
    print *,  'Final step'
    print *,  'N_det    = ', N_det
    print *,  'N_states = ', N_states
    do k=1,N_states
      print *, 'State', k
      print *,  'PT2      = ', pt2(k)
      print *,  'E        = ', E_CI_before(k)
      print *,  'E+PT2    = ', E_CI_before(k)+pt2(k)
      print *,  '-----'
    enddo
    call ezfio_set_cas_sd_zmq_energy(CI_energy(1))
    call ezfio_set_cas_sd_zmq_energy_pt2(E_CI_before(1)+pt2(1))
  endif

end
